"""Ensemble game outcome predictor: Elo + XGBoost classifier + XGBoost score regressor."""
import os
import math
import numpy as np
import joblib
from pathlib import Path
from xgboost import XGBClassifier, XGBRegressor
from sklearn.preprocessing import StandardScaler

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

WIN_MODEL_PATH = MODELS_DIR / "game_win_model.joblib"
SCORE_MODEL_PATH = MODELS_DIR / "game_score_model.joblib"
SCALER_PATH = MODELS_DIR / "game_scaler.joblib"

K_FACTOR = 20
HOME_ADVANTAGE_ELO = 65


def elo_win_probability(home_elo: float, away_elo: float) -> float:
    return 1.0 / (1.0 + 10 ** ((away_elo - home_elo - HOME_ADVANTAGE_ELO) / 400))


def update_elo(winner_elo: float, loser_elo: float, margin: int) -> tuple[float, float]:
    expected = 1.0 / (1.0 + 10 ** ((loser_elo - winner_elo) / 400))
    mov_multiplier = math.log(abs(margin) + 1) * (2.2 / ((winner_elo - loser_elo) * 0.001 + 2.2))
    new_winner = winner_elo + K_FACTOR * mov_multiplier * (1 - expected)
    new_loser = loser_elo + K_FACTOR * mov_multiplier * (0 - (1 - expected))
    return new_winner, new_loser


def load_or_create_models():
    if WIN_MODEL_PATH.exists() and SCORE_MODEL_PATH.exists():
        win_model = joblib.load(WIN_MODEL_PATH)
        score_model = joblib.load(SCORE_MODEL_PATH)
        scaler = joblib.load(SCALER_PATH) if SCALER_PATH.exists() else StandardScaler()
        return win_model, score_model, scaler

    win_model = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, eval_metric='logloss',
        use_label_encoder=False, random_state=42
    )
    score_model = XGBRegressor(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, eval_metric='mae',
        random_state=42
    )
    scaler = StandardScaler()
    return win_model, score_model, scaler


def predict_game(feature_vector: np.ndarray, home_elo: float, away_elo: float) -> dict:
    win_model, score_model, scaler = load_or_create_models()
    elo_prob = elo_win_probability(home_elo, away_elo)

    # If models not trained yet, fall back to Elo-only
    if not WIN_MODEL_PATH.exists():
        home_score = 23 + (home_elo + HOME_ADVANTAGE_ELO - away_elo) / 50
        away_score = 23 - (home_elo + HOME_ADVANTAGE_ELO - away_elo) / 50
        spread = home_score - away_score
        confidence = 0.5 + abs(elo_prob - 0.5) * 0.4
        return {
            "home_win_probability": round(elo_prob, 4),
            "away_win_probability": round(1 - elo_prob, 4),
            "predicted_home_score": round(max(7, home_score), 1),
            "predicted_away_score": round(max(7, away_score), 1),
            "predicted_total_points": round(home_score + away_score, 1),
            "predicted_spread": round(-spread, 1),
            "confidence_score": round(confidence, 4),
            "model_version": "elo-v1",
        }

    X = scaler.transform(feature_vector.reshape(1, -1))
    ml_prob = float(win_model.predict_proba(X)[0][1])
    scores = score_model.predict(X)[0]

    # Ensemble: 40% Elo + 60% ML
    home_win_prob = 0.4 * elo_prob + 0.6 * ml_prob
    home_score = float(scores[0]) if hasattr(scores, '__len__') else 23.0
    away_score = float(scores[1]) if hasattr(scores, '__len__') else 21.0
    confidence = 0.5 + abs(home_win_prob - 0.5) * 0.8

    return {
        "home_win_probability": round(home_win_prob, 4),
        "away_win_probability": round(1 - home_win_prob, 4),
        "predicted_home_score": round(max(7, home_score), 1),
        "predicted_away_score": round(max(7, away_score), 1),
        "predicted_total_points": round(home_score + away_score, 1),
        "predicted_spread": round(away_score - home_score, 1),
        "confidence_score": round(min(0.99, max(0.51, confidence)), 4),
        "model_version": "ensemble-v1",
    }


def monte_carlo_simulation(home_win_prob: float, predicted_home: float,
                            predicted_away: float, n_simulations: int = 10000) -> list[float]:
    """Run Monte Carlo sim, return list of simulated total scores."""
    rng = np.random.default_rng(42)
    home_std = max(7.0, predicted_home * 0.3)
    away_std = max(7.0, predicted_away * 0.3)
    home_scores = rng.normal(predicted_home, home_std, n_simulations).clip(0, 60)
    away_scores = rng.normal(predicted_away, away_std, n_simulations).clip(0, 60)
    totals = (np.round(home_scores) + np.round(away_scores)).tolist()
    return [int(t) for t in totals]


def compute_key_factors(feature_vector: np.ndarray, home_elo: float, away_elo: float) -> list[dict]:
    return [
        {
            "factor": "Elo Rating Differential",
            "favoredTeam": "home" if home_elo > away_elo else "away",
            "homeValue": str(round(home_elo)),
            "awayValue": str(round(away_elo)),
            "description": f"Home Elo {round(home_elo)} vs Away Elo {round(away_elo)} — {abs(round(home_elo - away_elo))} pt diff",
        },
        {
            "factor": "Recent Scoring (L4 PPG)",
            "favoredTeam": "home" if feature_vector[0] > feature_vector[2] else "away",
            "homeValue": str(round(float(feature_vector[0]), 1)),
            "awayValue": str(round(float(feature_vector[2]), 1)),
            "description": "Points scored per game over last 4 games",
        },
        {
            "factor": "Points Allowed (L4)",
            "favoredTeam": "away" if feature_vector[1] > feature_vector[3] else "home",
            "homeValue": str(round(float(feature_vector[1]), 1)),
            "awayValue": str(round(float(feature_vector[3]), 1)),
            "description": "Points allowed per game — lower is better",
        },
        {
            "factor": "EPA Per Play (L4)",
            "favoredTeam": "home" if feature_vector[12] > feature_vector[13] else "away",
            "homeValue": str(round(float(feature_vector[12]), 3)),
            "awayValue": str(round(float(feature_vector[13]), 3)),
            "description": "Expected Points Added per play — efficiency metric",
        },
        {
            "factor": "Home Field Advantage",
            "favoredTeam": "home",
            "homeValue": "+65 Elo pts",
            "awayValue": "N/A",
            "description": "Historically worth ~3 points and 65 Elo rating points",
        },
        {
            "factor": "Recent Form (Wins L4)",
            "favoredTeam": "home" if feature_vector[32] > feature_vector[33] else "away",
            "homeValue": f"{round(float(feature_vector[32]) * 4)}/4",
            "awayValue": f"{round(float(feature_vector[33]) * 4)}/4",
            "description": "Win-loss record over last 4 games",
        },
    ]
