from dotenv import load_dotenv
from typing import Optional
import os, json, requests, threading, time
from collections import defaultdict
from constants import LeagueTier, LeagueDivision, LeagueQueue

class PlayerMatchTimelineDownloader:
    def __init__(self):
        # Get the Riot Token, then set the token as a header param in request.Session
        self.session = requests.Session()
        self.__api_key = os.environ['RIOT_API_KEY']
        assert self.__api_key is not None
        self.session.headers.update({
            'X-Riot-Token': self.__api_key
        })
        self.high_tiers = {LeagueTier.CHALLENGER, LeagueTier.GRANDMASTER, LeagueTier.MASTER}
        self.high_tier_url = 'https://na1.api.riotgames.com/lol/league/v4/{tier}leagues/by-queue/{queue}'
        self.normal_tier_url = 'https://na1.api.riotgames.com/lol/league/v4/entries/{queue}/{tier}/{division}'

        # use threading lock to update rate limits
        self.lock = threading.Lock()

    
    def parse_rate_header(self, rate_header: str):
        '''
        Parses the 'X-Rate-Limit' header from Riot Endpoints to get the rate limits

        Returns a list of tuples (count, sec). Ex: rate_header = 20:1,100:120 means that user is
        allowed to call 20 times per second and 100 times per 2 minutes
        '''
        parts = []
        for rates in rate_header.split(','):
            count, sec = rates.split(':')
            parts.append((int(count), int(sec)))

        return parts

    def wait_for_request_slot(self, rate_limits: list[tuple[int, int]], rate_history: dict[list]):
        '''
        Blocks all requests until rate windows are within limits
        '''

        with self.lock:
            now = time.time()
            for limit, window in rate_limits:
                # Remove timestamps older than window
                rate_history[window] = [t for t in rate_history[window] if now - t < window]
                # If at limit, wait until the earliest timestamp expires
                if len(rate_history[window]) >= limit:
                    sleep_time = window - (now - rate_history[window][0]) + 0.01
                    time.sleep(sleep_time)

            for _, window in rate_limits:
                rate_history[window].append(time.time())
    
    def call_endpoint_with_rate_limit(self, url: str, rate_limits: list[tuple[int, int]], rate_history: dict[list], max_retries: int = 6):
        backoff = 0.5
        for _ in range(max_retries):
            try:
                self.wait_for_request_slot(rate_limits, rate_history)
                response = self.session.get(url)
                if response.status_code == 200:
                    if not rate_limits:
                        rate_limits.extend(self.parse_rate_header(response.headers.get('X-App-Rate-Limit', '')))
                    return response.json()
                elif response.status_code == 429:
                    retry_after = float(response.headers.get('Retry-After', 1))
                    print(f'Rate limited, sleeping for {retry_after}s...')
                    time.sleep(retry_after)
                else:
                    print(f'Server error {response.status_code}, retrying in {backoff}s...')
                    time.sleep(backoff)
                    backoff *= 2
                    response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print('Request Error:', e)

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
            
            start *= 10
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
    # Load the env variable 
    assert load_dotenv() == True
    # Get the top 1 challenger players from League-V4 API
    downloader = PlayerMatchTimelineDownloader()
        
    # Get a year's worth of match timeline from 1 Challenger players
    # downloader.download_n_players_rank_timeline(1, 'challenger_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.CHALLENGER)
    
    # Get a year's worth of match timeline from 1 Grandmaster players
    # downloader.download_n_players_rank_timeline(1, 'grandmaster_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.GRANDMASTER)
    
    # Get a year's worth of match timeline from 1 Master players
    # downloader.download_n_players_rank_timeline(1, 'master_timelines', LeagueQueue.RANKED_SOLO_5x5, LeagueTier.MASTER)
    
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