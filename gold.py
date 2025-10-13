from player_match import LeagueMatchTimelineAPI, RiotAPI
from constants import LANE_POSITION
def get_gold_difference(match_timeline: LeagueMatchTimelineAPI):
    '''
    Gets the gold difference of each role.
    Diff < 0 --> red player is winning
    Diff = 0 --> neutral
    Diff > 0 --> blue player is winning
    '''
    gold_diff = {i: [] for i in LANE_POSITION}
    for role in match_timeline.players_gold:
        for r_gold, b_gold in zip(match_timeline.players_gold[role]["Red"], match_timeline.players_gold[role]["Blue"]):
            gold_diff[role].append(b_gold-r_gold)

    return gold_diff


if __name__ == '__main__':
    api = RiotAPI()
    api.get_puuid('WotterMelown', 'NA1')
    match_arr = api.get_match_ids_by_puuid()
    api.get_match_by_id(match_arr)
    current_match_timeline = api.get_match_by_timeline(match_arr[0])
    match_timeline_api = LeagueMatchTimelineAPI(api.puuid, current_match_timeline)
    match_timeline_api.get_gold()
    print(get_gold_difference(match_timeline_api))