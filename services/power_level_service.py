import pandas as pd
import os, json
from collections import defaultdict
from libs.common.constants.league_constants import LeagueTier, LeagueDivision, LANE_POSITION
from typing import Optional
from libs.common.riot_rate_limit_api import RiotRateLimitAPI

class PowerLevelService(RiotRateLimitAPI):
    def __init__(self):
        super().__init__()
        self.match_url = 'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}'
        
    def extract_all_metrics(self, match_obj: dict, player_idx: int):
        '''Extracts all valuable metrics from the League Match-V5 API for power level and wrapped generation'''
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
        first_blood_taken = participants['firstBloodKill']
        role_position = LANE_POSITION[player_idx % 5]
        
        # OBJECTIVE PARTICIPATION (where player actually helped with objectives)
        heralds_killed = participants['challenges']['riftHeraldTakedowns'] 
        barons_killed = participants['challenges']['baronTakedowns'] 
        dragons_killed = participants['challenges']['dragonTakedowns']
        total_tower_destroyed = participants['challenges']['turretTakedowns']
        total_tower_plates_taken = participants['challenges']['turretPlatesTaken']   
        vision_score_per_minute = participants['challenges']['visionScorePerMinute']
        
        # === ADDITIONAL METRICS ===
        
        # GAME CONTEXT (Essential for normalization)
        game_duration = match_obj['info']['gameDuration']
        game_result = participants['win']
        game_minutes = game_duration / 60
        
        # MECHANICAL SKILL
        skillshots_hit = participants['challenges'].get('skillshotsHit', 0)
        skillshots_dodged = participants['challenges'].get('skillshotsDodged', 0)
        skillshot_accuracy = skillshots_hit / max(skillshots_hit + skillshots_dodged, 1)
        immobilize_and_kill = participants['challenges'].get('immobilizeAndKillWithAlly', 0)

        # CLUTCH MOMENTS & MULTI-KILLS
        solo_kills = participants['challenges'].get('soloKills', 0)
        outnumbered_kills = participants['challenges'].get('outnumberedKills', 0)
        double_kills = participants['doubleKills']
        triple_kills = participants['tripleKills']
        quadra_kills = participants['quadraKills']
        penta_kills = participants['pentaKills']
        total_multikills = double_kills + triple_kills + quadra_kills + penta_kills
        killing_sprees = participants['killingSprees']
        largest_killing_spree = participants['largestKillingSpree']

        # TEAMWORK & SYNERGY
        kill_participation = participants['challenges'].get('killParticipation', 0)
        full_team_takedowns = participants['challenges'].get('fullTeamTakedown', 0)
        save_ally_from_death = participants['challenges'].get('saveAllyFromDeath', 0)
        pick_kill_with_ally = participants['challenges'].get('pickKillWithAlly', 0)
        kill_after_hidden_with_ally = participants['challenges'].get('killAfterHiddenWithAlly', 0)

        # GAME IMPACT (Per-Minute Stats)
        damage_per_minute = participants['challenges'].get('damagePerMinute', 0)
        gold_per_minute = participants['challenges'].get('goldPerMinute', 0)
        team_damage_percentage = participants['challenges'].get('teamDamagePercentage', 0)
        damage_taken_on_team_percentage = participants['challenges'].get('damageTakenOnTeamPercentage', 0)

        # SURVIVABILITY
        longest_time_living = participants['longestTimeSpentLiving']
        time_spent_dead = participants['totalTimeSpentDead']
        deaths_by_enemy_champs = participants['challenges'].get('deathsByEnemyChamps', 0)
        survived_three_immobilizes = participants['challenges'].get('survivedThreeImmobilizesInFight', 0)

        # LATE GAME POWER
        legendary_items = participants['challenges'].get('legendaryItemUsed', [])
        legendary_count = len(legendary_items) if legendary_items else 0
        max_level_lead = participants['challenges'].get('maxLevelLeadLaneOpponent', 0)
        champ_level = participants['champLevel']

        # EARLY GAME
        first_blood_assist = participants['firstBloodAssist']
        takedowns_first_10min = participants['challenges'].get('takedownsFirstXMinutes', 0)
        early_laning_advantage = participants['challenges'].get('earlyLaningPhaseGoldExpAdvantage', 0)

        # CONTROL & CC
        time_ccing_others = participants['timeCCingOthers']
        enemy_immobilizations = participants['challenges'].get('enemyChampionImmobilizations', 0)

        # SPECIAL ACHIEVEMENTS
        flawless_aces = participants['challenges'].get('flawlessAces', 0)
        perfect_game = participants['challenges'].get('perfectGame', 0) 
        perfect_game = True if perfect_game else False
        
        return {
        # IDENTITY
        'champion_name': champion_name,
        'role_position': role_position,
        'champ_level': champ_level,
        
        # GAME CONTEXT
        'game_duration': game_duration,
        'game_minutes': game_minutes,
        'win': game_result,
        
        # CORE STATS
        'kills': total_kills,
        'deaths': total_deaths,
        'assists': total_assists,
        'kda': (total_kills + total_assists) / max(total_deaths, 1),
        
        # DAMAGE
        'total_damage_dealt': total_damage_dealt,
        'total_damage_taken': total_damage_taken,
        'damage_per_minute': damage_per_minute,
        'team_damage_percentage': team_damage_percentage,
        'damage_taken_on_team_percentage': damage_taken_on_team_percentage,
        
        # ECONOMY
        'total_gold': total_gold,
        'gold_per_minute': gold_per_minute,
        'cs_count': (cs_count),
        
        # VISION
        'vision_score': vision_score,
        'wards_placed': total_wards_placed,
        'wards_destroyed': total_wards_destroyed,
        'vision_score_per_minute': vision_score_per_minute,
        
        # OBJECTIVES
        'dragons_killed': dragons_killed,
        'barons_killed': barons_killed,
        'heralds_killed': heralds_killed,
        'turrets_destroyed': total_tower_destroyed,
        'turret_plates_taken': total_tower_plates_taken,
        
        # MECHANICAL SKILL
        'skillshots_hit': skillshots_hit,
        'skillshot_accuracy': skillshot_accuracy,
        'skillshots_dodged': skillshots_dodged,
        'immobilize_and_kill': immobilize_and_kill,
        
        # CLUTCH MOMENTS
        'solo_kills': solo_kills,
        'outnumbered_kills': outnumbered_kills,
        'double_kills': double_kills,
        'triple_kills': triple_kills,
        'quadra_kills': quadra_kills,
        'penta_kills': penta_kills,
        'killing_sprees': killing_sprees,
        'largest_killing_spree': largest_killing_spree,
        'first_blood_taken': first_blood_taken,
        'first_blood_assist': first_blood_assist,
        
        # TEAMWORK
        'kill_participation': kill_participation,
        'full_team_takedowns': full_team_takedowns,
        'save_ally_from_death': save_ally_from_death,
        'pick_kill_with_ally': pick_kill_with_ally,
        'kill_after_hidden': kill_after_hidden_with_ally,
        
        # SURVIVABILITY
        'longest_time_living': longest_time_living,
        'time_spent_dead': time_spent_dead,
        'survived_three_immobilizes': survived_three_immobilizes,
        'deaths_by_enemy_champs': deaths_by_enemy_champs,
        
        # CONTROL
        'time_ccing_others': time_ccing_others,
        'enemy_immobilizations': enemy_immobilizations,
        
        # PROGRESSION
        'legendary_items_count': legendary_count,
        'max_level_lead': max_level_lead,
        'takedowns_first_10min': takedowns_first_10min,
        
        # SPECIAL
        'flawless_aces': flawless_aces,
        'perfect_game': perfect_game,
    }
        
    def get_power_tier(self, score: int):
        """Power tier classifications"""
        if score >= 8500: return "LEGENDARY"
        if score >= 7000: return "MYTHIC"
        if score >= 5500: return "EPIC"
        if score >= 4000: return "RARE"
        if score >= 2500: return "UNCOMMON"
        return "COMMON"

    def calculate_power_level(self, metrics: dict):
        """
        Calculate power level (0-10,000) across 5 dimensions:
        Combat (30%), Objectives (25%), Vision (15%), Economy (15%), Clutch (15%)
        """
        role = metrics['role_position']
    
        # === COMBAT PROWESS (30%) - 0-3000 ===
        kda_score = min(metrics['kda'] * 250, 1000)
        damage_score = min(metrics['damage_per_minute'] * 0.9, 1000)
        team_damage_score = min(metrics['team_damage_percentage'] * 3000, 1000)
        combat = kda_score + damage_score + team_damage_score
        
        # === OBJECTIVES (25%) - 0-2500 ===
        objectives = min(
            metrics['dragons_killed'] * 250 +
            metrics['barons_killed'] * 450 +
            metrics['heralds_killed'] * 180 +
            metrics['turrets_destroyed'] * 120 +
            metrics['turret_plates_taken'] * 30,
            2500
        )
        
        # === VISION CONTROL (15%) - 0-1500 ===
        vision_multiplier = 1.6 if role == "SUPPORT" else 1.0
        vision = min(
            (metrics['vision_score'] * 18 + 
            metrics['wards_destroyed'] * 25) * vision_multiplier,
            1500
        )
        
        # === ECONOMY (15%) - 0-1500 ===
        economy = min(
            metrics['gold_per_minute'] * 2.2 +
            (metrics['cs_count'] / max(metrics['game_minutes'], 1)) * 12,
            1500
        )
        
        # === CLUTCH FACTOR (15%) - 0-1500 ===
        multikill_score = (
            metrics['double_kills'] * 100 +
            metrics['triple_kills'] * 300 +
            metrics['quadra_kills'] * 600 +
            metrics['penta_kills'] * 1000
        )
        
        clutch = min(
            metrics['solo_kills'] * 150 +
            metrics['outnumbered_kills'] * 200 +
            metrics['largest_killing_spree'] * 80 +
            multikill_score +
            (200 if metrics['first_blood_taken'] else 0) +
            metrics['flawless_aces'] * 400,
            1500
        )
        
        # === BONUSES & MULTIPLIERS ===
        base_total = combat + objectives + vision + economy + clutch
        
        # Win bonus
        if metrics['win']:
            base_total *= 1.15
        
        # Perfect game (no deaths, kills > 0)
        if metrics['perfect_game'] or (metrics['deaths'] == 0 and metrics['kills'] > 0):
            base_total *= 1.12
        
        # High kill participation
        if metrics['kill_participation'] >= 0.75:
            base_total *= 1.05
        
        total = int(min(base_total, 10000))
        
        return {
            'total': total,
            'tier': self.get_power_tier(total),
                'combat': int(min(combat, 3000)),
                'objectives': int(min(objectives, 2500)),
                'vision': int(min(vision, 1500)),
                'economy': int(min(economy, 1500)),
                'clutch': int(min(clutch, 1500))
        }
    
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

        # power_level_columns = ['match_id', 'total_gold', 'total_wards_placed', 'total_wards_destroyed', 
        #                     'vision_score', 'total_kills', 'total_deaths', 'total_assists', 
        #                     'total_tower_destroyed', 'heralds_killed', 'barons_killed', 'dragons_killed', 
        #                     'role_position', 'champion_name', 'total_damage_dealt', 'total_damage_taken', 'cs_count',
        #                     'first_blood_taken', 'total_tower_plates_taken']
        
        power_level_columns = ['match_id', 'power_level', 'power_tier', 'breakdown_combat', 'breakdown_objectives', 'breakdown_vision', 'breakdown_economy', 'breakdown_clutch']
        
        
        # win_prob_dataset = pd.DataFrame(columns=win_prob_dataset_columns)
        base_folder = os.path.join(os.getcwd(), match_folder_dir, f'{tier.value}_{f"{division.value}_" if division else ""}match_infos')
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
                        metrics = self.extract_all_metrics(match_obj, player_idx)
                        print(metrics)
                        input()
                        power_level = self.calculate_power_level(metrics)
                        print(power_level)
                        input()
                        # TODO: get vision score, total damage dealt, total damage received, kill participation, turret plate taken from match api
                        power_level_dataset.loc[len(power_level_dataset)] = power_level.values()
                        size += 1
                        if size % chunk_size == 0:
                            # append the rows to prevent memory overload on the pandas.df object
                            power_level.index = range(size, size + chunk_size)
                            power_level_dataset.to_csv(f'power_level_{puuid}.csv', mode='a', index_label='match_no', index=True, header=False)
                            # drop all rows
                            power_level_dataset.drop(power_level_dataset.index, inplace=True)

if __name__ == '__main__':
    power_level = PowerLevelService()
    power_level.preprocess('rank_match_info', 20, LeagueTier.CHALLENGER)
        