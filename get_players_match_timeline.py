from dotenv import load_dotenv
from typing import Optional
import os, json, requests
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
                    
                    normal_tier_response = self.session.get(self.normal_tier_url.format(tier=tier.value, queue=queue.value, divison=division.value))
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
        
    def download_players_match_timeline(self, puuid: str, count: int = 10):
        '''
        Downloads the players match timeline (defaults to 10 recent matches)
        '''
        # Get matches from puuid
        match_ids = self.get_match_ids_by_puuid(puuid, count=10)
        match_timelines = []
        for match_id in match_ids:
            match_timeline = self.get_match_by_timeline(match_id)
            match_timelines.append(match_timeline)
        
        with open(f'match_timeline_{puuid}.json', 'w+', encoding='utf-8') as f:
            f.write(json.dumps(match_timelines, indent=4))
        
            
            
        
        

if __name__ == '__main__':
    # Load the env variable 
    assert load_dotenv() == True
    # Get the top 10 challenger players from League-V4 API
    downloader = PlayerMatchTimelineDownloader()
    
    top_10_challengers = downloader.get_top_n_players_by_rank(10, LeagueQueue.RANKED_SOLO_5x5, LeagueTier.CHALLENGER)

    for p_challenger in top_10_challengers:
        downloader.download_players_match_timeline(p_challenger)
    