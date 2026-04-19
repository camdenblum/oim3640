"""FastAPI analytics microservice — NFL prediction engine."""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import query
from pipelines.feature_engineering import (
    build_game_feature_vector, get_elo_rating, build_player_feature_vector
)
from predictors.game_predictor import predict_game, monte_carlo_simulation, compute_key_factors
from predictors.player_predictor import predict_player, compute_matchup_rating, POSITION_STATS

app = FastAPI(title="NFL Predictor Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class GamePredictionRequest(BaseModel):
    game_id: int
    home_team_id: int
    away_team_id: int
    season_year: int
    week: int
    venue: Optional[str] = ""
    weather_temp_f: Optional[int] = 70
    weather_wind_mph: Optional[int] = 5


class PlayerPredictionRequest(BaseModel):
    player_id: int
    game_id: int
    opponent_team_id: int


class SimulationRequest(BaseModel):
    home_team_id: int
    away_team_id: int
    week: Optional[int] = 1
    n_simulations: Optional[int] = 10000


@app.get("/health")
def health():
    return {"status": "ok", "service": "nfl-analytics"}


@app.post("/predict/game")
async def predict_game_endpoint(request: GamePredictionRequest):
    try:
        feature_vector = build_game_feature_vector(
            request.home_team_id, request.away_team_id,
            request.season_year, request.week,
            request.venue or "", request.weather_temp_f or 70, request.weather_wind_mph or 5
        )
        home_elo = get_elo_rating(request.home_team_id)
        away_elo = get_elo_rating(request.away_team_id)

        prediction = predict_game(feature_vector, home_elo, away_elo)
        simulation = monte_carlo_simulation(
            prediction["home_win_probability"],
            prediction["predicted_home_score"],
            prediction["predicted_away_score"],
            10000
        )
        key_factors = compute_key_factors(feature_vector, home_elo, away_elo)

        return {
            **prediction,
            "simulation_distribution": simulation,
            "key_factors": key_factors,
            "model_inputs": {
                "home_elo": home_elo, "away_elo": away_elo,
                "week": request.week, "venue": request.venue,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/player")
async def predict_player_endpoint(request: PlayerPredictionRequest):
    player_rows = query("SELECT position FROM players WHERE id = %s", [request.player_id])
    if not player_rows:
        raise HTTPException(status_code=404, detail="Player not found")

    position = player_rows[0]['position']
    feature_vector = build_player_feature_vector(request.player_id, request.game_id, request.opponent_team_id)
    matchup_rating = compute_matchup_rating(position, request.opponent_team_id)

    result = predict_player(request.player_id, position, feature_vector, matchup_rating)
    return result


@app.post("/simulate/game")
async def simulate_game_endpoint(request: SimulationRequest):
    from datetime import datetime
    home_elo = get_elo_rating(request.home_team_id)
    away_elo = get_elo_rating(request.away_team_id)

    season_year = datetime.now().year if datetime.now().month >= 9 else datetime.now().year - 1
    fv = build_game_feature_vector(
        request.home_team_id, request.away_team_id,
        season_year, request.week or 1
    )

    prediction = predict_game(fv, home_elo, away_elo)
    simulation = monte_carlo_simulation(
        prediction["home_win_probability"],
        prediction["predicted_home_score"],
        prediction["predicted_away_score"],
        request.n_simulations or 10000
    )
    return {**prediction, "simulation_distribution": simulation}


@app.get("/model/accuracy")
async def get_model_accuracy():
    rows = query("""
        SELECT model_version,
            COUNT(*) as total,
            AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) as accuracy,
            AVG(absolute_error) as mae
        FROM model_accuracy_log GROUP BY model_version ORDER BY MAX(recorded_at) DESC
    """)
    return {"accuracy_data": [dict(r) for r in rows]}


@app.get("/model/feature-importance")
async def get_feature_importance():
    import joblib
    from predictors.game_predictor import MODELS_DIR, WIN_MODEL_PATH
    from pathlib import Path
    if not WIN_MODEL_PATH.exists():
        return {"importance": [], "message": "Model not yet trained"}
    model = joblib.load(WIN_MODEL_PATH)
    importance = model.feature_importances_.tolist()
    feature_names = [
        "home_ppg_l4", "home_ppg_allowed_l4", "away_ppg_l4", "away_ppg_allowed_l4",
        "home_ppg_l8", "away_ppg_l8", "home_yards_l4", "away_yards_l4",
        "home_pass_l4", "away_pass_l4", "home_rush_l4", "away_rush_l4",
        "home_epa_l4", "away_epa_l4", "home_3d_pct_l4", "away_3d_pct_l4",
        "home_rz_eff_l4", "away_rz_eff_l4", "home_to_l4", "away_to_l4",
        "home_to_l8", "away_to_l8", "home_sacks_l4", "away_sacks_l4",
        "home_pressure_l4", "away_pressure_l4", "home_field_adv",
        "surface", "dome", "temp_norm", "wind_norm", "week",
        "home_qb_injured", "away_qb_injured",
        "home_elo_norm", "away_elo_norm", "elo_diff",
        "home_wins_l4", "away_wins_l4", "h2h_win_pct", "home_momentum", "away_momentum",
    ]
    result = sorted(
        [{"feature": fn, "importance": float(imp)} for fn, imp in zip(feature_names, importance)],
        key=lambda x: x["importance"], reverse=True
    )
    return {"importance": result}


@app.post("/retrain")
async def trigger_retrain():
    import asyncio
    async def run_retrain():
        from updater import ModelUpdater
        u = ModelUpdater()
        u.update_elo_ratings()
        u.retrain_game_model()
    asyncio.create_task(run_retrain())
    return {"message": "Retraining started in background"}
