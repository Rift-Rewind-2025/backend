from dotenv import load_dotenv
from typing import Optional
import os, json, requests, threading, time
from collections import defaultdict
from constants import LeagueTier, LeagueDivision, LeagueQueue
from riot_rate_limit_api import RiotRateLimitAPI


class PlayerMatchTimelineDownloader(RiotRateLimitAPI):
    def __init__(self):
        super().__init__()
        self.high_tiers = {LeagueTier.CHALLENGER, LeagueTier.GRANDMASTER, LeagueTier.MASTER}
        self.high_tier_url = 'https://na1.api.riotgames.com/lol/league/v4/{tier}leagues/by-queue/{queue}'
        self.normal_tier_url = 'https://na1.api.riotgames.com/lol/league/v4/entries/{queue}/{tier}/{division}'


    def get_top_n_players_by_rank(self, n: int, queue: LeagueQueue, tier: LeagueTier, division: Optional[LeagueDivision] = None) -> list[str]:
        '''
        Gets the top N players (by LP or league points) within their rank (from tier and divison)
        Rank ranges from Iron up to Challenger
        Returns top N players PUUID of given rank
        '''
        
        # Check if the rank is Challenger or Grandmaster or Master
        try:
            if tier in self.high_tiers:
                # Call the high tier url with tier variable

                high_tier_response = self.session.get(self.high_tier_url.format(tier=tier.value, queue=queue.value))
                high_tier_response_json: dict = high_tier_response.json()
                high_tier_entries: list[dict] = high_tier_response_json.get('entries', [])
                high_tier_entries.sort(key=lambda x: x.get('leaguePoints', 0), reverse=True)
                high_tier_n_players = []
                
                for i in range(min(n, len(high_tier_entries))):
                    high_tier_n_players.append(high_tier_entries[i].get('puuid', ''))
                    
                return high_tier_n_players
            else:
                try:
                    assert division is not None
                    
                    normal_tier_response = self.session.get(self.normal_tier_url.format(tier=tier.value.upper(), queue=queue.value, division=division.value))
                    normal_tier_response_json: list[dict] = normal_tier_response.json()
                    normal_tier_response_json.sort(key=lambda x: x.get('leaguePoints', 0), reverse=True)
                    normal_tier_n_players = []
                    
                    for i in range(min(n, len(normal_tier_response_json))):
                        normal_tier_n_players.append(normal_tier_response_json[i].get('puuid', ''))
                        
                    return normal_tier_n_players
                except AssertionError as ae:
                    print('get_top_n_players_rank - AssertionError:', ae)
        except requests.exceptions.HTTPError as e:
            print('get_top_n_players_rank - HTTPError:', e)
            
    def get_match_ids_by_puuid(self, puuid: str, start: int = 0, count: int = 1) -> list[str]:
        try:
            match_ids_res = self.session.get(f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}')
            match_ids_res.raise_for_status()
            return match_ids_res.json()
        except requests.exceptions.HTTPError as e:
            print('get_match_ids_by_puuid - HTTPError:', e)
        
        return []
    
    def get_match_by_id(self, match_id: str) -> dict[str] | None:
        try:
            match_data = self.session.get(f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}')
            match_data.raise_for_status()
            return match_data.json()
        except requests.exceptions.HTTPError as e:
            print('Request Error:', e)
            
        return None

    def get_match_by_timeline(self, match_id: str)-> dict[str] | None:
        try:
            recent_match = self.session.get(f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline')
            recent_match.raise_for_status()
            return recent_match.json()
        except requests.exceptions.HTTPError as e:
            print('Request Error:', e)
            return None
        
    def download_players_yearly_match_timeline(self, puuid: str, save_directory: str, max_bulk_count: int = 200, count: int = 10):
        '''
        Downloads the players one year's worth of match timeline
        '''
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        
        if not os.path.exists(os.path.join(save_directory, puuid)):
            os.makedirs(os.path.join(save_directory, puuid))

        rate_limits = []
        rate_history = defaultdict(list)
        # Get matches from puuid
        start = 0
        bulk_count = 0
        now = time.time()
        last_match_timestamp = now
        while (now - last_match_timestamp) < 31536000 and bulk_count < max_bulk_count: # while the last match starts in less than a year, get the match timeline 
            match_ids = self.call_endpoint_with_rate_limit('https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}'.format(puuid=puuid, start=start, count=count), rate_limits, rate_history)
            match_timelines = []
            for match_id in match_ids:
                match_info = self.call_endpoint_with_rate_limit(f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}', rate_limits, rate_history)
                last_match_timestamp = match_info['info']['gameEndTimestamp']
                if (now - last_match_timestamp) > 31536000:
                    break
                match_timeline = self.call_endpoint_with_rate_limit(f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline', rate_limits, rate_history)
                match_timelines.append(match_timeline)

            with open(os.path.join(save_directory, puuid, f'match_timeline_bulk_{bulk_count}.json'), 'w+', encoding='utf-8') as f:
                f.write(json.dumps(match_timelines, indent=4))
            
            start += count
            bulk_count += 1
        
    def download_n_players_rank_timeline(self, n: int, save_directory: str, queue: LeagueQueue, tier: LeagueTier, division: Optional[LeagueDivision] = None):
        if not os.path.exists('rank_timelines'):
            os.makedirs('rank_timelines')
        
        # Get a year's worth of match timeline from N Challenger players
        top_n_players_by_rank = self.get_top_n_players_by_rank(n, queue, tier, division)
        time.sleep(1) # sleep for 1 second
        for p_player in top_n_players_by_rank:
            self.download_players_yearly_match_timeline(p_player, os.path.join('rank_timelines', save_directory), 200, 10)
            
        print(f"Successfully downloaded {n} player(s) year's worth of match timeline from {tier}{f' {division}' if division else ''} in {queue}!")
            
        
        

if __name__ == '__main__':
    # # Load the env variable 
    # assert load_dotenv() == True
    # Get the top 1 challenger players from League-V4 API
    downloader = PlayerMatchTimelineDownloader()
        
    # Get a year's worth of match timeline from 1 Challenger players
    downloader.download_n_players_rank_timeline(1, 'challenger_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.CHALLENGER)
    
    # Get a year's worth of match timeline from 1 Grandmaster players
    downloader.download_n_players_rank_timeline(1, 'grandmaster_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.GRANDMASTER)
    
    # Get a year's worth of match timeline from 1 Master players
    downloader.download_n_players_rank_timeline(1, 'master_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.MASTER)
    
    # Get a year's worth of match timeline from 1 Diamond players
    # downloader.download_n_players_rank_timeline(1, 'diamond_I_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.DIAMOND, LeagueDivision.I)
    downloader.download_n_players_rank_timeline(1, 'diamond_II_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.DIAMOND, LeagueDivision.II)
    # downloader.download_n_players_rank_timeline(1, 'diamond_III_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.DIAMOND, LeagueDivision.III)
    # downloader.download_n_players_rank_timeline(1, 'diamond_IV_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.DIAMOND, LeagueDivision.IV)
    
    # Get a year's worth of match timeline from 1 Emerald players
    # downloader.download_n_players_rank_timeline(1, 'emerald_I_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.EMERALD, LeagueDivision.I)
    downloader.download_n_players_rank_timeline(1, 'emerald_II_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.EMERALD, LeagueDivision.II)
    # downloader.download_n_players_rank_timeline(1, 'emerald_III_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.EMERALD, LeagueDivision.III)
    # downloader.download_n_players_rank_timeline(1, 'emerald_IV_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.EMERALD, LeagueDivision.IV)
    
    # Get a year's worth of match timeline from 1 Platinum players
    # downloader.download_n_players_rank_timeline(1, 'platinum_I_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.PLATINUM, LeagueDivision.I)
    downloader.download_n_players_rank_timeline(1, 'platinum_II_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.PLATINUM, LeagueDivision.II)
    # downloader.download_n_players_rank_timeline(1, 'platinum_III_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.PLATINUM, LeagueDivision.III)
    # downloader.download_n_players_rank_timeline(1, 'platinum_IV_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.PLATINUM, LeagueDivision.IV)
    
    # Get a year's worth of match timeline from 1 Gold players
    # downloader.download_n_players_rank_timeline(1, 'gold_I_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.GOLD, LeagueDivision.I)
    downloader.download_n_players_rank_timeline(1, 'gold_II_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.GOLD, LeagueDivision.II)
    # downloader.download_n_players_rank_timeline(1, 'gold_III_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.GOLD, LeagueDivision.III)
    # downloader.download_n_players_rank_timeline(1, 'gold_IV_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.GOLD, LeagueDivision.IV)
    
    # Get a year's worth of match timeline from 1 Silver players
    # downloader.download_n_players_rank_timeline(1, 'silver_I_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.SILVER, LeagueDivision.I)
    downloader.download_n_players_rank_timeline(1, 'silver_II_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.SILVER, LeagueDivision.II)
    # downloader.download_n_players_rank_timeline(1, 'silver_III_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.SILVER, LeagueDivision.III)
    # downloader.download_n_players_rank_timeline(1, 'silver_IV_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.SILVER, LeagueDivision.IV)
    
    # Get a year's worth of match timeline from 1 Bronze players
    # downloader.download_n_players_rank_timeline(1, 'bronze_I_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.BRONZE, LeagueDivision.I)
    downloader.download_n_players_rank_timeline(1, 'bronze_II_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.BRONZE, LeagueDivision.II)
    # downloader.download_n_players_rank_timeline(1, 'bronze_III_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.BRONZE, LeagueDivision.III)
    # downloader.download_n_players_rank_timeline(1, 'bronze_IV_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.BRONZE, LeagueDivision.IV)
    
    # Get a year's worth of match timeline from 1 Iron players
    # downloader.download_n_players_rank_timeline(1, 'iron_I_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.IRON, LeagueDivision.I)
    downloader.download_n_players_rank_timeline(1, 'iron_II_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.IRON, LeagueDivision.II)
    # downloader.download_n_players_rank_timeline(1, 'iron_III_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.IRON, LeagueDivision.III)
    # downloader.download_n_players_rank_timeline(1, 'iron_IV_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.IRON, LeagueDivision.IV)