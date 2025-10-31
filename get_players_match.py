from dotenv import load_dotenv
from typing import Optional
import os, json, requests, time
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict
from libs.common.constants.league_constants import LeagueTier, LeagueDivision, LeagueQueue
from libs.common.riot_rate_limit_api import RiotRateLimitAPI


class PlayerMatchDownloader(RiotRateLimitAPI):
    def __init__(self):
        super().__init__()
        self.high_tiers = {LeagueTier.CHALLENGER, LeagueTier.GRANDMASTER, LeagueTier.MASTER}
        self.high_tier_url = 'https://na1.api.riotgames.com/lol/league/v4/{tier}leagues/by-queue/{queue}'
        self.normal_tier_url = 'https://na1.api.riotgames.com/lol/league/v4/entries/{queue}/{tier}/{division}'
        self.match_puuid_v5_url = 'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}&startTime={startTime}&endTime={endTime}&type={type}'
        self.match_v5_url = 'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}'
        self.match_v5_info_url = 'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}/info'
        self.tz = ZoneInfo("America/Los_Angeles")

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
            
    def get_match_ids_by_puuid(self, puuid: str, start: int = 0, count: int = 10, startTime: Optional[int] = None, endTime: Optional[int] = None, type: Optional[str] = "") -> list[str]:
        try:
            match_ids_res = self.session.get(self.match_puuid_v5_url.format(puuid=puuid, start=start, count=count, startTime=startTime or "", endTime=endTime or "", type=type))
            match_ids_res.raise_for_status()
            return match_ids_res.json()
        except requests.exceptions.HTTPError as e:
            print('get_match_ids_by_puuid - HTTPError:', e)
        
        return []
    
    def get_match_by_id(self, match_id: str) -> dict[str] | None:
        try:
            match_data = self.session.get(self.match_v5_url.format(match_id=match_id))
            match_data.raise_for_status()
            return match_data.json()
        except requests.exceptions.HTTPError as e:
            print('Request Error:', e)
            
        return None

    def get_match_by_info(self, match_id: str)-> dict[str] | None:
        try:
            recent_match = self.session.get(self.match_v5_info_url.format(match_id=match_id))
            recent_match.raise_for_status()
            return recent_match.json()
        except requests.exceptions.HTTPError as e:
            print('Request Error:', e)
            return None
        
    def download_players_yearly_match_info(self, puuid: str, save_directory: str, count: int = 10):
        '''
        Downloads the players one year's worth of match info (RANKED ONLY, no tourneys or tutorials or normals)
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
        
        now = datetime.now(self.tz)
        last_year_from_now = None
        try:
            last_year_from_now = now.replace(year=now.year - 1)
        except ValueError:
            last_year_from_now = now.replace(year=now.year - 1, day=28)
        last_year_from_now = int(last_year_from_now.timestamp())
        now = int(now.timestamp())
        
        while len(match_ids_ranked := (self.call_endpoint_with_rate_limit(self.match_puuid_v5_url.format(puuid=puuid, start=start, count=count, startTime=last_year_from_now, endTime=now, type='ranked'), rate_limits, rate_history))) > 0:
            # get all the match-v5 objects from RANKED games
            match_obj = []
            for match_id in match_ids_ranked:
                match_info = self.call_endpoint_with_rate_limit(self.match_v5_url.format(match_id=match_id), rate_limits, rate_history)
                match_obj.append(match_info)
            # save the result in a json file
            with open(os.path.join(save_directory, puuid, f'match_info_bulk_{bulk_count}.json'), 'w+', encoding='utf-8') as f:
                f.write(json.dumps(match_obj, indent=4))
            
            start += count
            bulk_count += 1
        
    def download_n_players_rank_match_info(self, n: int, save_directory: str, queue: LeagueQueue, tier: LeagueTier, division: Optional[LeagueDivision] = None):
        if not os.path.exists('rank_match_info'):
            os.makedirs('rank_match_info')
        
        # Get a year's worth of match info from N Challenger players
        top_n_players_by_rank = self.get_top_n_players_by_rank(n, queue, tier, division)
        time.sleep(1) # sleep for 1 second
        for p_player in top_n_players_by_rank:
            self.download_players_yearly_match_info(p_player, os.path.join('rank_match_info', save_directory), 10)
            
        print(f"Successfully downloaded {n} player(s) year's worth of match info from {tier}{f' {division}' if division else ''} in {queue}!")
            
        
        

if __name__ == '__main__':
    # # Load the env variable 
    # assert load_dotenv() == True
    # Get the top 10 challenger players from League-V4 API
    downloader = PlayerMatchDownloader()
        
    # Get a year's worth of match info from 10 Challenger players
    downloader.download_n_players_rank_match_info(10, 'challenger_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.CHALLENGER)
    
    # Get a year's worth of match info from 10 Grandmaster players
    downloader.download_n_players_rank_match_info(10, 'grandmaster_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.GRANDMASTER)
    
    # Get a year's worth of match info from 10 Master players
    downloader.download_n_players_rank_match_info(10, 'master_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.MASTER)
    
    # Get a year's worth of match info from 10 Diamond players
    # downloader.download_n_players_rank_match_info(10, 'diamond_I_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.DIAMOND, LeagueDivision.I)
    downloader.download_n_players_rank_match_info(10, 'diamond_II_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.DIAMOND, LeagueDivision.II)
    # downloader.download_n_players_rank_match_info(10, 'diamond_III_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.DIAMOND, LeagueDivision.III)
    # downloader.download_n_players_rank_match_info(10, 'diamond_IV_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.DIAMOND, LeagueDivision.IV)
    
    # Get a year's worth of match info from 10 Emerald players
    # downloader.download_n_players_rank_match_info(10, 'emerald_I_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.EMERALD, LeagueDivision.I)
    downloader.download_n_players_rank_match_info(10, 'emerald_II_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.EMERALD, LeagueDivision.II)
    # downloader.download_n_players_rank_match_info(10, 'emerald_III_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.EMERALD, LeagueDivision.III)
    # downloader.download_n_players_rank_match_info(10, 'emerald_IV_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.EMERALD, LeagueDivision.IV)
    
    # Get a year's worth of match info from 10 Platinum players
    # downloader.download_n_players_rank_match_info(10, 'platinum_I_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.PLATINUM, LeagueDivision.I)
    downloader.download_n_players_rank_match_info(10, 'platinum_II_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.PLATINUM, LeagueDivision.II)
    # downloader.download_n_players_rank_match_info(10, 'platinum_III_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.PLATINUM, LeagueDivision.III)
    # downloader.download_n_players_rank_match_info(10, 'platinum_IV_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.PLATINUM, LeagueDivision.IV)
    
    # Get a year's worth of match info from 10 Gold players
    # downloader.download_n_players_rank_match_info(10, 'gold_I_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.GOLD, LeagueDivision.I)
    downloader.download_n_players_rank_match_info(10, 'gold_II_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.GOLD, LeagueDivision.II)
    # downloader.download_n_players_rank_match_info(10, 'gold_III_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.GOLD, LeagueDivision.III)
    # downloader.download_n_players_rank_match_info(10, 'gold_IV_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.GOLD, LeagueDivision.IV)
    
    # Get a year's worth of match info from 10 Silver players
    # downloader.download_n_players_rank_match_info(10, 'silver_I_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.SILVER, LeagueDivision.I)
    downloader.download_n_players_rank_match_info(10, 'silver_II_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.SILVER, LeagueDivision.II)
    # downloader.download_n_players_rank_match_info(10, 'silver_III_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.SILVER, LeagueDivision.III)
    # downloader.download_n_players_rank_match_info(10, 'silver_IV_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.SILVER, LeagueDivision.IV)
    
    # Get a year's worth of match info from 10 Bronze players
    # downloader.download_n_players_rank_match_info(10, 'bronze_I_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.BRONZE, LeagueDivision.I)
    downloader.download_n_players_rank_match_info(10, 'bronze_II_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.BRONZE, LeagueDivision.II)
    # downloader.download_n_players_rank_match_info(10, 'bronze_III_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.BRONZE, LeagueDivision.III)
    # downloader.download_n_players_rank_match_info(10, 'bronze_IV_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.BRONZE, LeagueDivision.IV)
    
    # Get a year's worth of match info from 10 Iron players
    # downloader.download_n_players_rank_match_info(10, 'iron_I_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.IRON, LeagueDivision.I)
    downloader.download_n_players_rank_match_info(10, 'iron_II_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.IRON, LeagueDivision.II)
    # downloader.download_n_players_rank_match_info(10, 'iron_III_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.IRON, LeagueDivision.III)
    # downloader.download_n_players_rank_match_info(10, 'iron_IV_match_infos', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.IRON, LeagueDivision.IV)