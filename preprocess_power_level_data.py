import pandas as pd
import os, json
from collections import defaultdict
from constants import LeagueTier, LeagueDivision, LANE_POSITION
from typing import Optional
from riot_rate_limit_api import RiotRateLimitAPI

class PowerLevelSystem(RiotRateLimitAPI):
    def __init__(self):
        super().__init__()
        self.match_url = 'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}'

    def preprocess(self, match_folder_dir: str, chunk_size: int, tier: LeagueTier, division: Optional[LeagueDivision] = None):
        # get the files from s3 (later)
        # for now, lets use local files
        # win_prob_dataset_columns = ['match_id', 'side', 'minute', 'team_gold_diff', 'team_gold_diff_delta60', 'team_kills_last60', 'team_deaths_last60',
        #                             'towers_diff', 'drakes_diff', 'heralds_diff', 'barons_diff', 'wards_ally_last60', 'wards_enemy_killed_last60', 'spent_recent_120s',
        #                             'unspent_flag', 'sec_to_next_drake', 'sec_to_next_herald', 'sec_to_next_baron',  'time_bucket_early', 'time_bucket_mid', 'time_bucket_late', 'patch_minor']
        # TODO: don't know if we need patch_minor column
        # TODO: should we do timestamp_ms or minute column? we can get timestamp in ms from match_timeline but don't know if it will be useful
        rate_limits = []
        rate_history = defaultdict(list)

        power_level_columns = ['match_id', 'total_gold', 'total_wards_placed', 'total_wards_destroyed', 
                            'vision_score', 'total_kills', 'total_deaths', 'total_assists', 
                            'total_tower_destroyed', 'heralds_killed', 'barons_killed', 'dragons_killed', 
                            'role_position', 'champion_name', 'total_damage_dealt', 'total_damage_taken', 'cs_count',
                            'first_blood_taken', 'total_tower_plates_taken']
        
        
        # win_prob_dataset = pd.DataFrame(columns=win_prob_dataset_columns)
        base_folder = os.path.join(os.getcwd(), match_folder_dir, f'{tier.value}_{f"{division.value}_" if division else ""}timelines')
        size = 0
        for puuid in os.listdir(base_folder):
            power_level_dataset = pd.DataFrame(columns=power_level_columns)
            power_level_dataset.to_csv(f'power_level_{puuid}.csv', index=True, header=True)
            for match_timelines_folder in os.listdir(os.path.join(base_folder, puuid)):
                # read in the file as a json object
                print(match_timelines_folder)
                with open(os.path.join(base_folder, puuid, match_timelines_folder), 'r', encoding='utf-8') as f:
                    match_timelines = json.load(f)
                    for match_timeline in match_timelines:
                        player_idx = match_timeline['metadata']['participants'].index(puuid)
                        match_id = match_timeline['metadata']['matchId']
                        
                        match_obj = self.call_endpoint_with_rate_limit(self.match_url.format(match_id=match_id), rate_limits, rate_history)
                        participants = match_obj['info']['participants'][player_idx]
                        vision_score = participants['visionScore']
                        champion_name = participants['championName']
                        total_damage_dealt = participants['totalDamageDealtToChampions']
                        total_damage_taken = participants['totalDamageTaken']
                        total_wards_placed = participants['wardsPlaced']
                        total_wards_destroyed = participants['wardsKilled']
                        cs_count = participants['totalMinionsKilled'] + participants['totalAllyJungleMinionsKilled'] + participants['totalEnemyJungleMinionsKilled']
                        total_kills = participants['kills']
                        total_assists = participants['assists']
                        total_deaths = participants['deaths']
                        total_gold = participants['goldEarned']
                        first_blood_taken = participants['firstBloodKill'] * 1
                        role_position = LANE_POSITION[player_idx % 5]
                        
                        # OBJECTIVE PARTICIPATION (where player actually helped with objectives)
                        heralds_killed = participants['challenges']['riftHeraldTakedowns'] 
                        barons_killed = participants['challenges']['baronTakedowns'] 
                        dragons_killed = participants['challenges']['dragonTakedowns']
                        total_tower_destroyed = participants['challenges']['turretTakedowns']
                        total_tower_plates_taken = participants['challenges']['turretPlatesTaken']                     
                        
                        # TODO: get vision score, total damage dealt, total damage received, kill participation, turret plate taken from match api
                        power_level_dataset.loc[len(power_level_dataset)] = [match_id, total_gold, total_wards_placed, total_wards_destroyed, 
                                                                            vision_score, total_kills, total_deaths, total_assists, total_tower_destroyed, 
                                                                            heralds_killed, barons_killed, dragons_killed, role_position, champion_name, 
                                                                            total_damage_dealt, total_damage_taken, cs_count, first_blood_taken, total_tower_plates_taken]
                        size += 1
                        if size % chunk_size == 0:
                            # append the rows to prevent memory overload on the pandas.df object
                            power_level_dataset.to_csv(f'power_level_{puuid}.csv', mode='a', index_label='match_no', index=True, header=False)
                            # drop all rows
                            power_level_dataset.drop(power_level_dataset.index, inplace=True)

if __name__ == '__main__':
    power_level = PowerLevelSystem()
    power_level.preprocess('rank_timelines', 20, LeagueTier.CHALLENGER)
        