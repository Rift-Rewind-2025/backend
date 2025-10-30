from player_match import LeagueMatchTimelineAPI, RiotAPI
from constants import LANE_POSITION
import requests
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

    participant_frame = match_timeline["info"]["frames"][closest_min]["participantFrames"].get(str(lane), {})
    curr_frame = match_timeline["info"]["frames"][closest_min]

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
if __name__ == '__main__':
    api = RiotAPI()
    api.get_puuid('WotterMelown', 'NA1')
    match_arr = api.get_match_ids_by_puuid()
    api.get_match_by_id(match_arr)
    current_match_timeline = api.get_match_by_timeline(match_arr[0])
    match_timeline_api = LeagueMatchTimelineAPI(api.puuid, current_match_timeline)
    match_timeline_api.get_gold()
    print(get_player_info(current_match_timeline,20,2)['final_items'])
