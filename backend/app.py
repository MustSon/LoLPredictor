# app.py
from flask import Flask, jsonify, request
from riot_api import RiotApiService
from flask_cors import CORS
import os
from dotenv import load_dotenv
import data_fetcher
import ml.predict as predict

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:5173"}}
)
load_dotenv()
RIOT_KEY = os.environ.get("riot_api_key")
riot = RiotApiService(api_key=RIOT_KEY)



@app.route("/api/summoner")
def get_summoner():
    game_name = request.args.get("gameName")
    tag_line = request.args.get("tagLine")

    account = riot.get_account_by_riot_id(game_name, tag_line)
    summoner = riot.get_summoner_by_puuid(account["puuid"])

    return summoner

@app.route("/api/recent-games")
def get_recent_games():
    game_name = request.args.get("gameName")
    tag_line = request.args.get("tagLine")


    if not game_name or not tag_line:
        return {"error": "Missing parameters"}, 400

    try:

        account = riot.get_account_by_riot_id(game_name, tag_line)
        puuid = account["puuid"]

        match_ids = riot.get_match_ids_by_puuid(puuid, count=10)
        if not match_ids:
            return {"message": "No recent matches"}, 200

        recent_games = []
        ranked_games_count = 0
        for mid in match_ids:
            match_data = riot.get_match_by_id(mid)

                        
            if match_data["info"]["queueId"] == 420:
                ranked_games_count+=1
                data = data_fetcher.extract_champions(match_data)
                recent_games.append({
                    "matchId": mid,
                    "participants": data
                })



        return jsonify({
            "recentGames": recent_games,
            "rankedGamesCount": ranked_games_count
            })

    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}, 500


@app.route("/api/predict")
def predict_game_outcome():
    team1 = request.args.get("team1").split(",")
    team2 = request.args.get("team2").split(",")

    result = predict.predict_match(team1,team2)


    return jsonify(result)




"""
@app.route("/api/active-game")
def get_active_game():
    game_name = request.args.get("gameName")
    tag_line = request.args.get("tagLine")

    if not game_name or not tag_line:
        return {"error": "Missing parameters"}, 400

    try:
        account = riot.get_account_by_riot_id(game_name, tag_line)
        puuid = account["puuid"]

        active_game = riot.get_active_game_by_puuid(puuid)
        if not active_game:
            return {"message": "No active game"}, 200

        champs = data_fetcher.extract_champions(active_game)

        return jsonify({"gameId": active_game["gameId"], "participants": champs})

    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}, 500
"""

if __name__ == "__main__":
    app.run(port=5000, debug=True)