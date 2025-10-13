import re
import pandas as pd

# === 1. Paste your raw match text here ===
raw_text = """
1. MATCH #NA1_5389135295
+++++++++++++++
Player 0
Champion: Urgot
Individual Positon: TOP
Role: SOLO
Lane: TOP
Team Position TOP
------------
Player 1
Champion: Zed
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 2
Champion: Sylas
Individual Positon: MIDDLE
Role: DUO
Lane: MIDDLE
Team Position MIDDLE
------------
Player 3
Champion: Jhin
Individual Positon: BOTTOM
Role: DUO
Lane: MIDDLE
Team Position BOTTOM
------------
Player 4
Champion: Nautilus
Individual Positon: UTILITY
Role: SUPPORT
Lane: MIDDLE
Team Position UTILITY
------------
Player 5
Champion: Riven
Individual Positon: TOP
Role: SOLO
Lane: TOP
Team Position TOP
------------
Player 6
Champion: Udyr
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 7
Champion: Jayce
Individual Positon: MIDDLE
Role: SOLO
Lane: MIDDLE
Team Position MIDDLE
------------
Player 8
Champion: Corki
Individual Positon: BOTTOM
Role: CARRY
Lane: BOTTOM
Team Position BOTTOM
------------
Player 9
Champion: Karma
Individual Positon: UTILITY
Role: SUPPORT
Lane: BOTTOM
Team Position UTILITY
------------
2. MATCH #NA1_5389028075
+++++++++++++++
Player 0
Champion: Fiora
Individual Positon: TOP
Role: SOLO
Lane: TOP
Team Position TOP
------------
Player 1
Champion: Zed
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 2
Champion: Riven
Individual Positon: MIDDLE
Role: SOLO
Lane: MIDDLE
Team Position MIDDLE
------------
Player 3
Champion: Syndra
Individual Positon: BOTTOM
Role: CARRY
Lane: BOTTOM
Team Position BOTTOM
------------
Player 4
Champion: KogMaw
Individual Positon: UTILITY
Role: SUPPORT
Lane: BOTTOM
Team Position UTILITY
------------
Player 5
Champion: Gragas
Individual Positon: TOP
Role: DUO
Lane: TOP
Team Position TOP
------------
Player 6
Champion: JarvanIV
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 7
Champion: Akali
Individual Positon: MIDDLE
Role: DUO
Lane: TOP
Team Position MIDDLE
------------
Player 8
Champion: Corki
Individual Positon: BOTTOM
Role: CARRY
Lane: BOTTOM
Team Position BOTTOM
------------
Player 9
Champion: Poppy
Individual Positon: UTILITY
Role: SUPPORT
Lane: BOTTOM
Team Position UTILITY
------------
3. MATCH #NA1_5388973431
+++++++++++++++
Player 0
Champion: Darius
Individual Positon: TOP
Role: DUO
Lane: TOP
Team Position TOP
------------
Player 1
Champion: Nidalee
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 2
Champion: Jayce
Individual Positon: MIDDLE
Role: CARRY
Lane: MIDDLE
Team Position MIDDLE
------------
Player 3
Champion: Riven
Individual Positon: BOTTOM
Role: DUO
Lane: TOP
Team Position BOTTOM
------------
Player 4
Champion: Nautilus
Individual Positon: UTILITY
Role: SUPPORT
Lane: MIDDLE
Team Position UTILITY
------------
Player 5
Champion: Yorick
Individual Positon: TOP
Role: DUO
Lane: TOP
Team Position TOP
------------
Player 6
Champion: Viego
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 7
Champion: Ahri
Individual Positon: MIDDLE
Role: DUO
Lane: TOP
Team Position MIDDLE
------------
Player 8
Champion: Jhin
Individual Positon: BOTTOM
Role: CARRY
Lane: BOTTOM
Team Position BOTTOM
------------
Player 9
Champion: Bard
Individual Positon: UTILITY
Role: SUPPORT
Lane: BOTTOM
Team Position UTILITY
------------
4. MATCH #NA1_5388925998
+++++++++++++++
Player 0
Champion: Urgot
Individual Positon: TOP
Role: SOLO
Lane: TOP
Team Position TOP
------------
Player 1
Champion: Taliyah
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 2
Champion: Corki
Individual Positon: MIDDLE
Role: CARRY
Lane: MIDDLE
Team Position MIDDLE
------------
Player 3
Champion: Jhin
Individual Positon: BOTTOM
Role: SOLO
Lane: BOTTOM
Team Position BOTTOM
------------
Player 4
Champion: Blitzcrank
Individual Positon: UTILITY
Role: SUPPORT
Lane: MIDDLE
Team Position UTILITY
------------
Player 5
Champion: Kled
Individual Positon: TOP
Role: DUO
Lane: TOP
Team Position TOP
------------
Player 6
Champion: Rengar
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 7
Champion: Vladimir
Individual Positon: MIDDLE
Role: SOLO
Lane: MIDDLE
Team Position MIDDLE
------------
Player 8
Champion: Zyra
Individual Positon: BOTTOM
Role: DUO
Lane: TOP
Team Position BOTTOM
------------
Player 9
Champion: DrMundo
Individual Positon: UTILITY
Role: SOLO
Lane: BOTTOM
Team Position UTILITY
------------
5. MATCH #NA1_5388898850
+++++++++++++++
Player 0
Champion: Rumble
Individual Positon: TOP
Role: SUPPORT
Lane: NONE
Team Position TOP
------------
Player 1
Champion: Volibear
Individual Positon: JUNGLE
Role: SUPPORT
Lane: NONE
Team Position JUNGLE
------------
Player 2
Champion: Syndra
Individual Positon: MIDDLE
Role: SUPPORT
Lane: NONE
Team Position MIDDLE
------------
Player 3
Champion: Senna
Individual Positon: BOTTOM
Role: SUPPORT
Lane: NONE
Team Position BOTTOM
------------
Player 4
Champion: DrMundo
Individual Positon: UTILITY
Role: SUPPORT
Lane: NONE
Team Position UTILITY
------------
Player 5
Champion: Ambessa
Individual Positon: TOP
Role: SUPPORT
Lane: NONE
Team Position TOP
------------
Player 6
Champion: JarvanIV
Individual Positon: JUNGLE
Role: SUPPORT
Lane: NONE
Team Position JUNGLE
------------
Player 7
Champion: Sylas
Individual Positon: MIDDLE
Role: SUPPORT
Lane: NONE
Team Position MIDDLE
------------
Player 8
Champion: Smolder
Individual Positon: BOTTOM
Role: SUPPORT
Lane: NONE
Team Position BOTTOM
------------
Player 9
Champion: Soraka
Individual Positon: UTILITY
Role: SUPPORT
Lane: NONE
Team Position UTILITY
------------
6. MATCH #NA1_5388861030
+++++++++++++++
Player 0
Champion: Rumble
Individual Positon: TOP
Role: DUO
Lane: TOP
Team Position TOP
------------
Player 1
Champion: XinZhao
Individual Positon: JUNGLE
Role: SOLO
Lane: BOTTOM
Team Position JUNGLE
------------
Player 2
Champion: Syndra
Individual Positon: MIDDLE
Role: CARRY
Lane: MIDDLE
Team Position MIDDLE
------------
Player 3
Champion: Sivir
Individual Positon: BOTTOM
Role: DUO
Lane: TOP
Team Position BOTTOM
------------
Player 4
Champion: Nidalee
Individual Positon: UTILITY
Role: SUPPORT
Lane: MIDDLE
Team Position UTILITY
------------
Player 5
Champion: Yorick
Individual Positon: TOP
Role: SOLO
Lane: TOP
Team Position TOP
------------
Player 6
Champion: Sylas
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 7
Champion: Yone
Individual Positon: MIDDLE
Role: SOLO
Lane: MIDDLE
Team Position MIDDLE
------------
Player 8
Champion: Kaisa
Individual Positon: BOTTOM
Role: NONE
Lane: JUNGLE
Team Position BOTTOM
------------
Player 9
Champion: Nami
Individual Positon: UTILITY
Role: SOLO
Lane: BOTTOM
Team Position UTILITY
------------
8. MATCH #NA1_5388526543
+++++++++++++++
Player 0
Champion: Chogath
Individual Positon: TOP
Role: SOLO
Lane: TOP
Team Position TOP
------------
Player 1
Champion: Kindred
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 2
Champion: Ahri
Individual Positon: MIDDLE
Role: DUO
Lane: MIDDLE
Team Position MIDDLE
------------
Player 3
Champion: Corki
Individual Positon: BOTTOM
Role: DUO
Lane: MIDDLE
Team Position BOTTOM
------------
Player 4
Champion: Blitzcrank
Individual Positon: UTILITY
Role: SUPPORT
Lane: MIDDLE
Team Position UTILITY
------------
Player 5
Champion: Fiora
Individual Positon: TOP
Role: NONE
Lane: JUNGLE
Team Position TOP
------------
Player 6
Champion: Zyra
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 7
Champion: Diana
Individual Positon: MIDDLE
Role: SOLO
Lane: MIDDLE
Team Position MIDDLE
------------
Player 8
Champion: Smolder
Individual Positon: BOTTOM
Role: CARRY
Lane: BOTTOM
Team Position BOTTOM
------------
Player 9
Champion: Kennen
Individual Positon: UTILITY
Role: SUPPORT
Lane: BOTTOM
Team Position UTILITY
------------
9. MATCH #NA1_5388508171
+++++++++++++++
Player 0
Champion: DrMundo
Individual Positon: TOP
Role: DUO
Lane: MIDDLE
Team Position TOP
------------
Player 1
Champion: Talon
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 2
Champion: Galio
Individual Positon: MIDDLE
Role: DUO
Lane: MIDDLE
Team Position MIDDLE
------------
Player 3
Champion: Lucian
Individual Positon: BOTTOM
Role: CARRY
Lane: BOTTOM
Team Position BOTTOM
------------
Player 4
Champion: Sona
Individual Positon: UTILITY
Role: SUPPORT
Lane: BOTTOM
Team Position UTILITY
------------
Player 5
Champion: Jax
Individual Positon: TOP
Role: SOLO
Lane: TOP
Team Position TOP
------------
Player 6
Champion: Diana
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 7
Champion: Riven
Individual Positon: MIDDLE
Role: SOLO
Lane: MIDDLE
Team Position MIDDLE
------------
Player 8
Champion: Karthus
Individual Positon: BOTTOM
Role: CARRY
Lane: BOTTOM
Team Position BOTTOM
------------
Player 9
Champion: Senna
Individual Positon: UTILITY
Role: SUPPORT
Lane: BOTTOM
Team Position UTILITY
------------
10. MATCH #NA1_5388464165
+++++++++++++++
Player 0
Champion: DrMundo
Individual Positon: TOP
Role: SOLO
Lane: TOP
Team Position TOP
------------
Player 1
Champion: Sylas
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 2
Champion: Vladimir
Individual Positon: MIDDLE
Role: SOLO
Lane: MIDDLE
Team Position MIDDLE
------------
Player 3
Champion: Sivir
Individual Positon: BOTTOM
Role: CARRY
Lane: BOTTOM
Team Position BOTTOM
------------
Player 4
Champion: Neeko
Individual Positon: UTILITY
Role: SUPPORT
Lane: BOTTOM
Team Position UTILITY
------------
Player 5
Champion: Yone
Individual Positon: TOP
Role: SOLO
Lane: TOP
Team Position TOP
------------
Player 6
Champion: Zyra
Individual Positon: JUNGLE
Role: NONE
Lane: JUNGLE
Team Position JUNGLE
------------
Player 7
Champion: Riven
Individual Positon: MIDDLE
Role: SOLO
Lane: MIDDLE
Team Position MIDDLE
------------
Player 8
Champion: Ahri
Individual Positon: BOTTOM
Role: CARRY
Lane: BOTTOM
Team Position BOTTOM
------------
Player 9
Champion: Senna
Individual Positon: UTILITY
Role: SUPPORT
Lane: BOTTOM
Team Position UTILITY
------------
"""

# === 2. Regex patterns ===
match_pattern = re.compile(r"MATCH\s+#(NA1_\d+)")
player_pattern = re.compile(
    r"Player\s+(\d+)\s+Champion:\s+(\w+)\s+Individual Positon:\s+(\w+)"
    r"\s+Role:\s+(\w+)\s+Lane:\s+(\w+)\s+Team Position\s+(\w*)"
)

# === 3. Parse text ===
matches = match_pattern.split(raw_text)[1:]  # skip leading empty split
rows = []

for i in range(0, len(matches), 2):
    match_id = matches[i]
    players_block = matches[i + 1]
    for player in player_pattern.findall(players_block):
        player_num, champ, indiv_pos, role, lane, team_pos = player
        rows.append({
            "Match ID": match_id,
            "Player": int(player_num),
            "Champion": champ,
            "Individual Position": indiv_pos,
            "Role": role,
            "Lane": lane,
            "Team Position": team_pos
        })

# === 4. Create DataFrame and save as CSV ===
df = pd.DataFrame(rows)
df.to_csv("match_data_2.csv", index=False)

print("✅ CSV file 'match_data.csv' created successfully!")