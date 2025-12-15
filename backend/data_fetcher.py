from fastapi import FastAPI
from dotenv import load_dotenv
from riot_api import RiotApiService
import os
import json
import pandas as pd
import requests
import time

def extract_champions(match_data):
    data2 = json.dumps(match_data, indent  =2 )
    participants = match_data["info"]["participants"]
    result = []
    for p in participants:
        result.append({
            "teamId": p.get("teamId"),
            "championName": p.get("championName"),
            "summonerName": f"{p.get('riotIdGameName', '')}#{p.get('riotIdTagline', '')}",
            "win" : p.get("win"),
        })
    return result




def fetch_data():
    load_dotenv()
    RIOT_KEY = os.environ.get("riot_api_key")

    riot_service = RiotApiService(api_key = RIOT_KEY )
    while True:
        wait_time = 20
        for remaining in range(wait_time, 0, -1):
            print(f"Wait for {remaining} seconds...", end="\r")
            time.sleep(1)
        output_file = "./data/data.xlsx"

        if os.path.exists(output_file):
            df_existing = pd.read_excel(output_file)
            all_match_rows = df_existing.to_dict(orient="records")
            if all_match_rows:
                start_puuid = all_match_rows[-1]["puuid"]
            else:
                start_puuid = puuid
        else:
            all_match_rows = []
            start_puuid = puuid
        

        

        matches = riot_service.crawl_matches(start_puuid=start_puuid, total_matches=15)



        for i, m in enumerate(matches):

            if m["info"]["queueId"] != 420:
                print(f"Match {m['metadata']['matchId']} skipped. Not Solo Q")
                continue

            match_rank = None

            for p in m["info"]["participants"]:
                puuid_p = p["puuid"]
                try:
                    print("ok")
                    rank = riot_service.get_rank(puuid_p)
                except requests.HTTPError as e:
                    print(f"Error receiving rank for {puuid_p}: {e}")
                    rank = None

                if rank is not None:
                    match_rank = rank
                    print("gefunden")
                    break

            if match_rank is None:
                print(f"Match {m['metadata']['matchId']} skipped!!! None of players has a current actual rank")
                continue

            for p in m["info"]["participants"]:
                puuid_p = p["puuid"]
                summoner_name = f"{p['riotIdGameName']}#{p['riotIdTagline']}"
                champ = p.get("championName")
                kills = p.get("kills")
                dmg = p.get("totalDamageDealtToChampions")
                win = p.get("win")

                match_row = {
                    "puuid": puuid_p,
                    "summoner_name": summoner_name,
                    "champion": champ,
                    "rank": match_rank,
                    "kills": kills,
                    "damage": dmg,
                    "win": win,
                    "match_id": m["metadata"]["matchId"],
                    "most_common_rank": match_rank
                }

                if not any(row["summoner_name"] == summoner_name and row["match_id"] == m["metadata"]["matchId"] 
                        for row in all_match_rows):
                    all_match_rows.append(match_row)

            df = pd.DataFrame(all_match_rows)
            df.to_excel(output_file, index=False)
            print(f"Match {i+1} gespeichert: {m['metadata']['matchId']} mit Rank: {match_rank}")