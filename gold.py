from player_match import LeagueMatchTimelineAPI, RiotAPI
from constants import LANE_POSITION
import requests
import random
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

def get_player_info(match_timeline: dict, minute: int, lane: int):
    """
    Simulates player's inventory up to the given minute,
    handling purchases, destroys, sells, and undos correctly.
    """
    total_minutes = len(match_timeline["info"]["frames"]) - 1
    closest_min = min(total_minutes, max(0, minute - 1))

    curr_frame = match_timeline["info"]["frames"][closest_min]
    participant_frame = curr_frame["participantFrames"].get(str(lane), {})

    player_info = {
        "level": participant_frame.get("level"),
        "xp": participant_frame.get("xp"),
        "gold": participant_frame.get("totalGold"),
        "items_purchased": [],
        "items_destroyed": [],
        "skills_leveled": [],
        "final_items": []
    }

    inventory = []  # simulate live inventory

    # Iterate chronologically through frames and events
    for frame in match_timeline["info"]["frames"]:
        if frame["timestamp"] > curr_frame["timestamp"]:
            break

        for event in frame.get("events", []):
            if event.get("participantId") != lane:
                continue

            etype = event.get("type")
            item_id = event.get("itemId")

            if etype == "ITEM_PURCHASED":
                player_info["items_purchased"].append(item_id)
                inventory.append(item_id)

            elif etype in ("ITEM_DESTROYED", "ITEM_SOLD"):
                player_info["items_destroyed"].append(item_id)
                if item_id in inventory:
                    inventory.remove(item_id)

            elif etype == "ITEM_UNDO":
                before = event.get("beforeId")
                after = event.get("afterId")
                # Remove the undone item
                if before and before in inventory:
                    inventory.remove(before)
                # If undo reverts to another item (like switching a component), add back afterId
                if after and after != 0:
                    inventory.append(after)

            elif etype == "SKILL_LEVEL_UP":
                player_info["skills_leveled"].append(event["skillSlot"])

    # Final items at this minute (after all corrections)
    player_info["final_items"] = _get_items_with_tags(inventory)
    return player_info

def _get_items_with_tags(item_ids, patch_version="14.20.1", language="en_US"):
    """
    Given a list of item IDs (from match_timeline),
    return a dictionary mapping each ID -> {'name': ..., 'tags': ...}
    """
    url = f"https://ddragon.leagueoflegends.com/cdn/{patch_version}/data/{language}/item.json"
    data = requests.get(url).json()
    item_data = data["data"]

    result = {}
    for item_id in item_ids:
        str_id = str(item_id)
        if str_id in item_data:
            item_info = item_data[str_id]
            result[item_id] = {
                "name": item_info.get("name"),
                #"tags": item_info.get("tags", [])
            }
        else:
            result[item_id] = {"name": None}  # fallback for removed/unreleased items

    return result

def get_participant_id(match_data, puuid):
    """
    Return the participantId (1–10) for a given player's PUUID.
    """
    for p in match_data["info"]["participants"]:
        if p["puuid"] == puuid:
            return p["participantId"]
    return None

def get_player_lane(match_data, participant_id):
    """
    Return (lane, championName, teamId) for a given participantId.
    """
    for p in match_data["info"]["participants"]:
        if p["participantId"] == participant_id:
            lane = p.get("teamPosition") or p.get("lane") or "UNKNOWN"
            champ = p.get("championName", "Unknown Champ")
            team_id = p.get("teamId")
            return lane, champ, team_id
    return "UNKNOWN", "Unknown Champ", None

def find_laner(match_data, lane, player_team_id):
    """
    Find the opposing champion in the same lane (the laner).
    """
    for p in match_data["info"]["participants"]:
        if p.get("teamPosition") == lane and p.get("teamId") != player_team_id:
            return p["participantId"], p["championName"]
    return None, None
def play_gold_quiz_for_user(api, match_data, match_timeline):
    """
    Personalized quiz comparing the user's champion vs their laner.
    """
    # --- Identify Player ---
    player_id = get_participant_id(match_timeline, api.puuid)
    if not player_id:
        print("Could not find player in match metadata.")
        return

    lane, champ, player_team_id = get_player_lane(match_data, player_id)
    laner_id, laner_champ = find_laner(match_data, lane, player_team_id)

    if not laner_id:
        print("No laner found (e.g., jungle/ARAM game). Skipping.")
        return

    # --- Random minute (10–25) ---
    minute = random.randint(10, 25)

    # --- Get player and laner info ---
    player_info = get_player_info(match_timeline, minute, player_id)
    laner_info = get_player_info(match_timeline, minute, laner_id)

    # --- Display quiz ---
    print(f"\nMinute {minute} — {lane} Lane Quiz!")
    print(f"You ({champ}) vs {laner_champ}")

    print("\nYour build:")
    for item in player_info["final_items"].values():
        if item["name"]:
            print(f" • {item['name']}")
    print(f"Gold: ??? (hidden!)")

    print("\nLaner’s build:")
    for item in laner_info["final_items"].values():
        if item["name"]:
            print(f" • {item['name']}")
    print(f"Gold: ??? (hidden!)")

    # --- Ask question ---
    answer = input("\nWho has more gold? (you/laner): ").strip().lower()

    correct = (
        (player_info["gold"] > laner_info["gold"] and answer == "you") or
        (laner_info["gold"] > player_info["gold"] and answer == "laner")
    )

    print("\nCorrect!" if correct else "\n❌ Wrong!")
    print(f"Final Gold — You: {player_info['gold']:,} | Laner: {laner_info['gold']:,}")

if __name__ == '__main__':
    api = RiotAPI()
    api.get_puuid('WotterMelown', 'NA1')
    match_arr = api.get_match_ids_by_puuid()

    # Fetch the match data (populate match_list)
    api.get_match_by_id(match_arr)           # previously missing
    match_data = api.match_list[0]           # now safe
    current_match_timeline = api.get_match_by_timeline(match_arr[0])

    # Optional: compute gold per lane (not strictly needed for quiz)
    match_timeline_api = LeagueMatchTimelineAPI(api.puuid, current_match_timeline)
    match_timeline_api.get_gold()

    # Play the gold quiz
    play_gold_quiz_for_user(api, match_data, current_match_timeline)
