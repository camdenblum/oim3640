"""Model retraining pipeline. Run weekly after games complete."""
import math
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from datetime import datetime
from xgboost import XGBClassifier, XGBRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss, mean_absolute_error

from db import query, execute
from pipelines.feature_engineering import build_game_feature_vector, get_elo_rating
from predictors.game_predictor import update_elo, MODELS_DIR

MODELS_DIR.mkdir(exist_ok=True)


class ModelUpdater:
    def retrain_game_model(self):
        print(f"[{datetime.now()}] Retraining game model...")
        rows = query("""
            SELECT g.id, g.home_team_id, g.away_team_id, g.season_year, g.week,
                   g.venue, g.weather_temp_f, g.weather_wind_mph,
                   g.home_score, g.away_score
            FROM games g WHERE g.status = 'final' AND g.season_type = 'regular'
              AND g.home_score IS NOT NULL ORDER BY g.season_year, g.week
        """)
        if len(rows) < 50:
            print("Insufficient data for training. Need at least 50 games.")
            return

        X, y_win, y_home_score, y_away_score = [], [], [], []
        for row in rows:
            try:
                fv = build_game_feature_vector(
                    row['home_team_id'], row['away_team_id'],
                    row['season_year'], row['week'],
                    row['venue'] or '', row['weather_temp_f'] or 65,
                    row['weather_wind_mph'] or 5
                )
                home_win = 1 if row['home_score'] > row['away_score'] else 0
                X.append(fv)
                y_win.append(home_win)
                y_home_score.append(float(row['home_score']))
                y_away_score.append(float(row['away_score']))
            except Exception as e:
                print(f"Skipping game {row['id']}: {e}")

        if len(X) < 50:
            return

        X = np.array(X)
        y_win = np.array(y_win)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Walk-forward cross-validation
        tscv = TimeSeriesSplit(n_splits=4)
        best_logloss = float('inf')
        best_win_model, best_score_model = None, None

        for train_idx, val_idx in tscv.split(X_scaled):
            X_tr, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_tr, y_val = y_win[train_idx], y_win[val_idx]

            win_model = XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.05,
                                       subsample=0.8, colsample_bytree=0.8,
                                       eval_metric='logloss', use_label_encoder=False, random_state=42)
            win_model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
            ll = log_loss(y_val, win_model.predict_proba(X_val)[:, 1])

            if ll < best_logloss:
                best_logloss = ll
                best_win_model = win_model

                y_tr_home = np.array(y_home_score)[train_idx]
                score_model = XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
                                            random_state=42)
                score_model.fit(X_tr, y_tr_home)
                best_score_model = score_model

        if best_win_model:
            joblib.dump(best_win_model, MODELS_DIR / "game_win_model.joblib")
            joblib.dump(best_score_model, MODELS_DIR / "game_score_model.joblib")
            joblib.dump(scaler, MODELS_DIR / "game_scaler.joblib")
            print(f"Game model saved. Best log-loss: {best_logloss:.4f}")

    def update_elo_ratings(self):
        print("Updating Elo ratings...")
        rows = query("""
            SELECT g.id, g.home_team_id, g.away_team_id, g.home_score, g.away_score
            FROM games g WHERE g.status = 'final' AND g.season_type = 'regular'
            ORDER BY g.season_year, g.week
        """)
        elo = {}
        for row in rows:
            h, a = row['home_team_id'], row['away_team_id']
            if h not in elo:
                elo[h] = get_elo_rating(h)
            if a not in elo:
                elo[a] = get_elo_rating(a)
            hs, as_ = row['home_score'], row['away_score']
            if hs > as_:
                elo[h], elo[a] = update_elo(elo[h] + 65, elo[a], hs - as_)
                elo[h] -= 65
            elif as_ > hs:
                elo[a], elo[h] = update_elo(elo[a], elo[h] + 65, as_ - hs)
                elo[h] -= 65

        for team_id, rating in elo.items():
            execute("UPDATE elo_ratings SET rating = %s, updated_at = NOW() WHERE team_id = %s",
                    [rating, team_id])
        print(f"Updated Elo for {len(elo)} teams")


if __name__ == '__main__':
    updater = ModelUpdater()
    updater.update_elo_ratings()
    updater.retrain_game_model()
