import pandas as pd
import joblib

model = joblib.load("./data/lol_model.pkl")
champ_stats = joblib.load("./data/champ_stats.pkl")
global_avg = joblib.load("./data/global_avg.pkl")


def predict_match(team1_champs, team2_champs):
    r1 = champ_stats.reindex(team1_champs)['win_rate'].fillna(global_avg)
    r2 = champ_stats.reindex(team2_champs)['win_rate'].fillna(global_avg)

    features = pd.DataFrame([{
        'team1_avg_strength': r1.mean(),
        'team1_best_champ': r1.max(),
        'team1_has_op': int((r1 > 0.55).any()),
        'team1_has_weak': int((r1 < 0.45).any()),
        'team2_avg_strength': r2.mean(),
        'team2_best_champ': r2.max(),
        'team2_has_op': int((r2 > 0.55).any()),
        'team2_has_weak': int((r2 < 0.45).any()),
        'strength_diff': r1.mean() - r2.mean(),
        'best_champ_diff': r1.max() - r2.max(),
        'op_diff': int((r1 > 0.55).any()) - int((r2 > 0.55).any()),
        'weak_diff': int((r1 < 0.45).any()) - int((r2 < 0.45).any()),
    }])

    win_prob = model.predict_proba(features)[0][1]

    return win_prob
