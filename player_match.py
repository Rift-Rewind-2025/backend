from api import RiotAPI
from constants import LANE_POSITION

class LeagueMatchTimelineAPI:
    ''' API per match timeline'''
    def __init__(self, puuid: str, match_timeline: dict[str]):
        self.match_timeline = match_timeline
        self.minutes_played = len(match_timeline['info']['frames'])
        self.id = match_timeline['metadata']['matchId']
        self.current_player_idx = match_timeline['metadata']['participants'].index(puuid)
        self.players_pos = {i: {"Red": [], "Blue": []} for i in LANE_POSITION}
        # info -> frames -> participantFrames[1:10] -> position[x],position[y]
        self.players_gold = {i: {"Red": [], "Blue": []} for i in LANE_POSITION}

    def get_players_position(self):
        for frame in self.match_timeline['info']['frames']:
            for participant_frame in frame['participantFrames']:
                p_frame = int(participant_frame) - 1
                self.players_pos[LANE_POSITION[p_frame % 5]]["Blue" if p_frame < 5 else "Red"].append((frame['participantFrames'][participant_frame]['position']['x'], frame['participantFrames'][participant_frame]['position']['y']))
    def get_gold(self):
        for frame in self.match_timeline['info']['frames']:
            for participant_frame in frame['participantFrames']:
                p_frame = int(participant_frame) - 1
                self.players_gold[LANE_POSITION[p_frame % 5]]["Blue" if p_frame < 5 else "Red"].append((frame['participantFrames'][participant_frame]['totalGold']))




if __name__ == '__main__':
    api = RiotAPI()
    api.get_puuid('WotterMelown', 'NA1')
    match_arr = api.get_match_ids_by_puuid()
    api.get_match_by_id(match_arr)
    current_match_timeline = api.get_match_by_timeline(match_arr[0])
    leagueMatch = LeagueMatchTimelineAPI(api.puuid, current_match_timeline)
    leagueMatch.get_gold()