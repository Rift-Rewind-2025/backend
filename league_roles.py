import api

api = api.RiotAPI()
api.get_puuid('cant type', '1998')
match_arr = api.get_match_ids_by_puuid(start = 0, count = 10)
api.get_match_by_id(match_arr)
for idx, match in enumerate(api.match_list):
    if match["info"]["gameMode"] == "CLASSIC":
        print(f'{idx + 1}. MATCH #{match['metadata']['matchId']}')
        print('+++++++++++++++')
        #info -> participants[0-9] -> championName, individualPosition, role, lane, teamPosition
        for i, players in enumerate(match['info']['participants']):
            print("Player", i)
            print(f"Champion: {players['championName']}")
            print(f"Individual Positon: {players['individualPosition']}")
            print(f"Role: {players['role']}")
            print(f"Lane: {players['lane']}")
            print(f"Team Position {players['teamPosition']}")
            print("------------")



