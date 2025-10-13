import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

LANE_POSITION = ("Top", "Jungle", "Middle", "Bottom", "Utility")

class RiotAPI:
    def __init__(self):
        self.puuid = None
        self.__api_key = os.environ['RIOT_API_KEY']
        assert self.__api_key is not None
        self.match_list = list()
        self.session = requests.Session()
        self.session.headers.update({
            'X-Riot-Token': self.__api_key,
        })



    def get_puuid(self, gameName: str, tagName: str) -> None:
        try:
            puuid_res = self.session.get(f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagName}')
            puuid_res.raise_for_status()
            self.puuid = puuid_res.json()["puuid"]
        except requests.exceptions.HTTPError as e:
            print('Request Error:', e)


    def get_match_ids_by_puuid(self, start: int = 0, count: int = 1) -> list[str]:
        try:
            assert self.puuid is not None
            match_ids_res = self.session.get(f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{self.puuid}/ids?start={start}&count={count}')

            if match_ids_res.ok:
                return match_ids_res.json()
            return []
        except requests.exceptions.HTTPError as e:
            print('Request Error:', e)
        except AssertionError:
            print('Error: PUUID is not set!')

    def get_match_by_id(self, match_arr: list[str]):
        try:
            for matches in match_arr:
                match_data = self.session.get(f'https://americas.api.riotgames.com/lol/match/v5/matches/{matches}')
                match_data.raise_for_status()
                self.match_list.append(match_data.json())
        except requests.exceptions.HTTPError as e:
            print('Request Error:', e)


    def get_match_by_timeline(self, match_id: str)-> dict[str]:
        try:
            recent_match = self.session.get(f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline')
            recent_match.raise_for_status()
            return recent_match.json()
        except requests.exceptions.HTTPError as e:
            print('Request Error:', e)





if __name__ == '__main__':
    api = RiotAPI()
    api.get_puuid('WotterMelown', 'NA1')
    match_arr = api.get_match_ids_by_puuid()
    api.get_match_by_id(match_arr)
    current_match_timeline = api.get_match_by_timeline(match_arr[0])
    player_team = ""
    blueTeam = []
    redTeam = []
    for i in range(10):
        curr_participant = current_match_timeline["metadata"]["participants"][i]
        if i < 5:
            if api.puuid == curr_participant:
                player_team = "Blue"
            blueTeam.append(curr_participant)
        else:
            if api.puuid == curr_participant:
                player_team = "Red"
            redTeam.append(curr_participant)

    print(blueTeam, redTeam, player_team)








