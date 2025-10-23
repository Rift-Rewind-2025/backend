import pandas as pd
import os, json
from constants import LeagueTier, LeagueDivision, LANE_POSITION
from typing import Optional

def main(match_folder_dir: str, tier: LeagueTier, division: Optional[LeagueDivision] = None):
    # get the files from s3 (later)
    # for now, lets use local files
    # win_prob_dataset_columns = ['match_id', 'side', 'minute', 'team_gold_diff', 'team_gold_diff_delta60', 'team_kills_last60', 'team_deaths_last60',
    #                             'towers_diff', 'drakes_diff', 'heralds_diff', 'barons_diff', 'wards_ally_last60', 'wards_enemy_killed_last60', 'spent_recent_120s',
    #                             'unspent_flag', 'sec_to_next_drake', 'sec_to_next_herald', 'sec_to_next_baron',  'time_bucket_early', 'time_bucket_mid', 'time_bucket_late', 'patch_minor']
    # TODO: don't know if we need patch_minor column
    # TODO: should we do timestamp_ms or minute column? we can get timestamp in ms from match_timeline but don't know if it will be useful
    
    power_level_columns = ['match_id', 'total_gold', 'total_wards_placed', 'total_wards_destroyed', 
                           'vision_score', 'total_kills', 'total_deaths', 'total_assists', 
                           'total_tower_destroyed', 'heralds_killed', 'barons_killed', 'dragons_killed', 
                           'role_position', 'champion_name', 'total_damage_dealt', 'total_damage_taken', 'cs_count',
                           'first_blood_taken', 'total_tower_plates_taken']
    
    power_level_dataset = pd.DataFrame(columns=power_level_columns)
    # win_prob_dataset = pd.DataFrame(columns=win_prob_dataset_columns)
    print(power_level_dataset)
    base_folder = os.path.join(os.getcwd(), match_folder_dir, f'{tier.value}_{f"{division.value}_" if division else ""}timelines')
    for puuid in os.listdir(base_folder):
        
        for match_timelines_folder in os.listdir(os.path.join(base_folder, puuid)):
            # read in the file as a json object
            with open(os.path.join(base_folder, puuid, match_timelines_folder), 'r', encoding='utf-8') as f:
                match_timelines = json.load(f)
                # for match_timeline in match_timelines:
                #     player_idx = match_timeline['metadata']['participants'].index(puuid)
                #     match_id = match_timeline['metadata']['matchId']
                #     team_side = 'blue' if player_idx < 5 else 'red'
                #     prev_gold_diff = [0, 0]
                #     blue_tower_taken, red_tower_taken = 0, 0 # amount of towers taken from blue and red team
                    
                #     for frames in match_timeline['info']['frames']:
                #         # get team gold difference for both teams
                #         gold_diff = [0, 0] # [blue, red]
                #         for partiFrames in frames['participantFrames']:
                #             p_frames = int(partiFrames) - 1
                #             gold_diff[(p_frames >= 5) * 1] += frames['participantFrames'][partiFrames]['totalGold']
                #         # get team kills last 60s
                #         # get team deaths last 60s
                #         team_deaths = [0, 0] # [blue, red]
                #         team_kills = [0, 0] # [blue, red]
                #         for event in frames['events']:
                #             if event['type'] in ['CHAMPION_KILL', 'CHAMPION_SPECIAL_KILL']:
                #                 killer_id = event['killerId'] - 1
                #                 team_kills[(killer_id >= 5) * 1] += 1
                #                 team_deaths[(killer_id < 5) * 1] += 1 # the opposite
                                
                #         # do blue side
                #         win_prob_dataset.loc[idx, 'match_id'] = match_id
                #         win_prob_dataset.loc[idx, 'timestamp_ms'] = frames['timestamp']
                #         win_prob_dataset.loc[idx, 'side'] = 'blue'
                #         win_prob_dataset.loc[idx, 'team_gold_diff'] = gold_diff[0] - gold_diff[1]
                #         # get the difference in gold difference for each team
                #         win_prob_dataset.loc[idx, 'team_gold_diff_delta60'] = gold_diff[0] - prev_gold_diff[0]
                #         win_prob_dataset.loc[]
                
                for idx, match_timeline in enumerate(match_timelines):
                    player_idx = match_timeline['metadata']['participants'].index(puuid)
                    match_id = match_timeline['metadata']['matchId']
                    total_gold = match_timeline['info']['frames'][-1]['participantFrames'][str(player_idx + 1)]['totalGold']
                    # TODO: should I combine both minionsKilled and jungleMinionsKilled counts together?
                    cs_count = match_timeline['info']['frames'][-1]['participantFrames'][str(player_idx + 1)]['minionsKilled']
                    total_kills = total_deaths = total_assists = total_tower_destroyed = heralds_killed = barons_killed = dragons_killed = total_tower_plates_taken = 0
                    total_damage_dealt = total_damage_taken = total_wards_placed = total_wards_destroyed = 0
                    first_blood_taken = 0
                    role_position = LANE_POSITION[player_idx % 5]
                    champion_name = None
                    for frames in match_timeline['info']['frames']:
                        for event in frames['events']:
                            if event['type'] in ['CHAMPION_KILL', 'CHAMPION_SPECIAL_KILL']:
                                killer_id = event['killerId'] - 1
                                victim_id = event.get('victimId', 0) - 1
                                if event.get('killType', '') == 'FIRST_BLOOD_KILL' and player_idx == killer_id:
                                    first_blood_taken += 1
                                    continue
                                # if user killed another player
                                if player_idx == killer_id:
                                    total_kills += 1
                                    # get total damage dealt
                                    # TODO: this might be wrong because the pariticpantIds don't match up
                                    for victim_damage_dealt in event.get('victimDamageDealt', []):
                                        p_id = victim_damage_dealt['participantId'] - 1
                                        if player_idx == p_id:
                                            total_damage_dealt += victim_damage_dealt['physicalDamage'] + victim_damage_dealt['magicDamage']
                                
                                # if user was killed by another player
                                if player_idx == victim_id:
                                    total_deaths += 1
                                     # get total damage taken
                                     # TODO: this might be wrong because the pariticpantIds don't match up
                                    for victim_damage_dealt in event.get('victimDamageReceived', []):
                                        p_id = victim_damage_dealt['participantId'] - 1
                                        if player_idx == p_id:
                                            total_damage_dealt += victim_damage_dealt['physicalDamage'] + victim_damage_dealt['magicDamage']
                                    
                                # if user participated in the kill (assist)
                                if (player_idx + 1) in event.get('assistingParticipantIds', []):
                                    total_assists += 1

                            elif event['type'] == 'BUILDING_KILL':
                                killerId = event['killerId'] - 1
                                if player_idx == killerId or (player_idx + 1) in event.get('assistingParticipantIds', []):
                                    total_tower_destroyed += 1
                                
                                # TODO: find count of tower plates taken and minute first tower plate was taken
                            elif event['type'] == 'ELITE_MONSTER_KILL':
                                monster_type = event.get('monsterType', '')
                                killerId = event['killerId'] - 1
                                
                                if player_idx == killerId or (player_idx + 1) in event.get('assistingParticipantIds', []):
                                    if monster_type == 'RIFTHERALD':
                                        heralds_killed += 1
                                    elif monster_type == 'BARON_NASHOR':
                                        barons_killed += 1
                                    elif monster_type in ['DRAGON', 'ELDER_DRAGON']:
                                        dragons_killed += 1
                            elif event['type'] == 'TURRET_PLATE_DESTROYED':
                                killerId = event['killerId'] - 1
                                if player_idx == killer_id:
                                    total_tower_plates_taken += 1
                            elif event['type'] == 'WARD_PLACED':
                                creator_id = event['creatorId'] - 1
                                if player_idx == creator_id:
                                    total_wards_placed += 1
                            elif event['type'] == 'WARD_KILL':
                                killerId = event['killerId'] - 1
                                if player_idx == killer_id:
                                    total_wards_destroyed += 1
                    # TODO: get vision score
                    power_level_dataset.loc[len(power_level_dataset)] = [match_id, total_gold, total_kills, total_wards_placed, total_wards_destroyed, total_deaths, total_assists]
    
    

if __name__ == '__main__':
    main()
        