import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import warnings
import time
warnings.filterwarnings('ignore')


start = time.time()
df = pd.read_excel("data_clean.xlsx")
df["win"] = df["win"].replace({"WAHR": 1, "FALSCH": 0}).astype(int)
df["team"] = df.groupby("match_id").cumcount() // 5

print(f"📊 {df['match_id'].nunique()} matches loaded")
print()

match_ids = df['match_id'].unique()
train_ids, test_ids = train_test_split(
    match_ids,
    test_size=0.2,
    random_state=42
)

train_df = df[df['match_id'].isin(train_ids)]
test_df  = df[df['match_id'].isin(test_ids)]

champ_stats = train_df.groupby('champion')['win'].agg(['mean', 'count'])
champ_stats.columns = ['win_rate', 'games_played']

global_avg = champ_stats['win_rate'].mean()



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

    return {
        'team1_win_chance': f"{win_prob:.1%}",
        'team2_win_chance': f"{(1 - win_prob):.1%}",
        'predicted_winner': 'Team 1' if win_prob > 0.5 else 'Team 2',
        'confidence': 'High' if abs(win_prob - 0.5) > 0.2 else
                      'Medium' if abs(win_prob - 0.5) > 0.1 else 'Low',
        'key_factors': [
            f"Team strength: {'Team 1 stronger' if r1.mean() > r2.mean() else 'Team 2 stronger'}",
            f"Strongest champ: {'Team 1 better' if r1.max() > r2.max() else 'Team 2 better'}",
            f"OP champs: {'Both' if (r1 > 0.55).any() and (r2 > 0.55).any() else 'Team 1' if (r1 > 0.55).any() else 'Team 2' if (r2 > 0.55).any() else 'Neither'}",
            f"Weak champs: {'Both' if (r1 < 0.45).any() and (r2 < 0.45).any() else 'Team 1' if (r1 < 0.45).any() else 'Team 2' if (r2 < 0.45).any() else 'Neither'}"
        ]
    }



def build_matches(data):
    matches = []
    for match_id in data['match_id'].unique():
        m = data[data['match_id'] == match_id]
        t1 = m[m['team'] == 0]
        t2 = m[m['team'] == 1]

        c1 = t1['champion'].tolist()
        c2 = t2['champion'].tolist()

        r1 = champ_stats.reindex(c1)['win_rate'].fillna(global_avg)
        r2 = champ_stats.reindex(c2)['win_rate'].fillna(global_avg)

        matches.append({
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
            'team1_won': t1['win'].iloc[0]
        })

    return pd.DataFrame(matches)

train_matches = build_matches(train_df)
test_matches  = build_matches(test_df)

X_train = train_matches.drop(columns=['team1_won'])
y_train = train_matches['team1_won']
X_test  = test_matches.drop(columns=['team1_won'])
y_test  = test_matches['team1_won']

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=5,
    random_state=42
)

model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print(f"Model Accuracy: {accuracy:.1%}")
print(f"Baseline: {y_train.mean():.1%}")
print(f"Time taken: {time.time() - start:.1f} seconds")

team1 = ['Caitlyn', 'Jarvan IV', 'Viktor', 'Leona', 'Ornn']
team2 = ['Draven', 'Viego', 'Lissandra', 'Bard', 'Sett']

result = predict_match(team1, team2)
print("Team 1:", ", ".join(team1))
print("Team 2:", ", ".join(team2))
print()
print("Prediction:", result['predicted_winner'])
print("Team 1 win chance:", result['team1_win_chance'])
print("Team 2 win chance:", result['team2_win_chance'])

import joblib

joblib.dump(model, "lol_model.pkl")
joblib.dump(champ_stats, "champ_stats.pkl")
joblib.dump(global_avg, "global_avg.pkl")
