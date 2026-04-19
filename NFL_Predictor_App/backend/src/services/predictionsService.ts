import axios from 'axios';
import { pool } from '../database/connection';
import { getCurrentNFLSeason, getCurrentNFLWeek } from './espnService';
import { logger } from '../config/logger';

const analyticsUrl = process.env.ANALYTICS_SERVICE_URL || 'http://localhost:8001';

export class PredictionsService {
  async getWeekPredictions(week?: number) {
    const w = week || getCurrentNFLWeek();
    const s = getCurrentNFLSeason();
    const { rows: games } = await pool.query(`
      SELECT g.id FROM games g WHERE g.season_year = $1 AND g.week = $2
    `, [s, w]);

    const predictions = await Promise.all(games.map(g => this.getGamePrediction(g.id)));
    return predictions.filter(Boolean);
  }

  async getGamePrediction(gameId: number) {
    // Check stored prediction first
    const { rows } = await pool.query(`
      SELECT gp.*, g.*, ht.name as home_name, ht.abbreviation as home_abbr, ht.primary_color as home_color,
        at2.name as away_name, at2.abbreviation as away_abbr, at2.primary_color as away_color
      FROM game_predictions gp
      JOIN games g ON g.id = gp.game_id
      JOIN teams ht ON ht.id = g.home_team_id JOIN teams at2 ON at2.id = g.away_team_id
      WHERE gp.game_id = $1 ORDER BY gp.predicted_at DESC LIMIT 1
    `, [gameId]);

    if (rows.length) return rows[0];

    // Generate fresh prediction
    return this.generateGamePrediction(gameId);
  }

  async generateGamePrediction(gameId: number) {
    const { rows: games } = await pool.query(
      'SELECT * FROM games WHERE id = $1', [gameId]
    );
    if (!games.length) return null;
    const game = games[0];

    try {
      const response = await axios.post(`${analyticsUrl}/predict/game`, {
        game_id: gameId,
        home_team_id: game.home_team_id,
        away_team_id: game.away_team_id,
        season_year: game.season_year,
        week: game.week,
        venue: game.venue,
        weather_temp_f: game.weather_temp_f,
        weather_wind_mph: game.weather_wind_mph,
      }, { timeout: 30000 });

      const pred = response.data;
      await pool.query(`
        INSERT INTO game_predictions (game_id, model_version, home_win_probability, away_win_probability,
          predicted_home_score, predicted_away_score, predicted_total_points, predicted_spread,
          confidence_score, key_factors, model_inputs, simulation_distribution)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
      `, [gameId, pred.model_version, pred.home_win_probability, pred.away_win_probability,
          pred.predicted_home_score, pred.predicted_away_score, pred.predicted_total_points,
          pred.predicted_spread, pred.confidence_score, JSON.stringify(pred.key_factors),
          JSON.stringify(pred.model_inputs), JSON.stringify(pred.simulation_distribution)]);

      return pred;
    } catch (err) {
      logger.warn(`Analytics service unavailable for game ${gameId}, using Elo fallback`);
      return this.eloFallbackPrediction(gameId);
    }
  }

  async eloFallbackPrediction(gameId: number) {
    const { rows } = await pool.query(`
      SELECT g.*, he.rating as home_elo, ae.rating as away_elo,
        ht.name as home_name, ht.abbreviation as home_abbr,
        at2.name as away_name, at2.abbreviation as away_abbr
      FROM games g
      LEFT JOIN elo_ratings he ON he.team_id = g.home_team_id
      LEFT JOIN elo_ratings ae ON ae.team_id = g.away_team_id
      JOIN teams ht ON ht.id = g.home_team_id JOIN teams at2 ON at2.id = g.away_team_id
      WHERE g.id = $1
    `, [gameId]);
    if (!rows.length) return null;
    const g = rows[0];
    const homeElo = g.home_elo || 1500;
    const awayElo = g.away_elo || 1500;
    const eloDiff = homeElo + 65 - awayElo; // 65 = home field advantage
    const homeWinProb = 1 / (1 + Math.pow(10, -eloDiff / 400));
    return {
      game_id: gameId,
      home_name: g.home_name, away_name: g.away_name,
      home_win_probability: homeWinProb,
      away_win_probability: 1 - homeWinProb,
      predicted_home_score: 23 + (eloDiff / 100),
      predicted_away_score: 23 - (eloDiff / 100),
      predicted_total_points: 46,
      predicted_spread: -(eloDiff / 25),
      confidence_score: 0.55,
      model_version: 'elo-fallback-v1',
      key_factors: [{ factor: 'Elo Rating Differential', homeValue: String(homeElo.toFixed(0)), awayValue: String(awayElo.toFixed(0)) }],
    };
  }

  async getGamePlayerProjections(gameId: number) {
    const { rows } = await pool.query(`
      SELECT pp.*, p.full_name, p.position, p.jersey_number, t.abbreviation as team_abbr
      FROM player_predictions pp
      JOIN players p ON p.id = pp.player_id JOIN teams t ON t.id = p.team_id
      WHERE pp.game_id = $1 ORDER BY pp.confidence_score DESC
    `, [gameId]);
    return rows;
  }

  async getPlayerProjection(playerId: number) {
    const { rows } = await pool.query(`
      SELECT pp.* FROM player_predictions pp
      JOIN games g ON g.id = pp.game_id WHERE pp.player_id = $1 AND g.status = 'scheduled'
      ORDER BY pp.predicted_at DESC LIMIT 1
    `, [playerId]);
    return rows[0] || null;
  }

  async getSeasonProjection(teamId: number) {
    const { rows } = await pool.query(`
      SELECT t.name, t.abbreviation,
        COUNT(CASE WHEN g.status = 'final' AND ((g.home_team_id = $1 AND g.home_score > g.away_score) OR (g.away_team_id = $1 AND g.away_score > g.home_score)) THEN 1 END) as wins,
        COUNT(CASE WHEN g.status = 'final' THEN 1 END) as games_played,
        17 - COUNT(CASE WHEN g.status = 'final' THEN 1 END) as games_remaining,
        e.rating as elo
      FROM teams t
      LEFT JOIN games g ON (g.home_team_id = t.id OR g.away_team_id = t.id) AND g.season_year = $2
      LEFT JOIN elo_ratings e ON e.team_id = t.id
      WHERE t.id = $1 GROUP BY t.id, e.rating
    `, [teamId, getCurrentNFLSeason()]);
    return rows[0];
  }

  async getPlayoffProbabilities() {
    const { rows } = await pool.query(`
      SELECT t.id, t.name, t.abbreviation, t.conference, t.division, e.rating as elo,
        COUNT(CASE WHEN g.status = 'final' AND ((g.home_team_id = t.id AND g.home_score > g.away_score) OR (g.away_team_id = t.id AND g.away_score > g.home_score)) THEN 1 END) as wins,
        COUNT(CASE WHEN g.status = 'final' THEN 1 END) as games_played
      FROM teams t
      LEFT JOIN games g ON (g.home_team_id = t.id OR g.away_team_id = t.id) AND g.season_year = $1 AND g.season_type = 'regular'
      LEFT JOIN elo_ratings e ON e.team_id = t.id
      WHERE t.deleted_at IS NULL
      GROUP BY t.id, e.rating ORDER BY t.conference, wins DESC
    `, [getCurrentNFLSeason()]);

    return rows.map(t => ({
      ...t,
      playoff_probability: Math.min(0.99, Math.max(0.01, ((t.wins || 0) / Math.max(t.games_played || 1, 1)) * 0.8 + ((t.elo || 1500) - 1300) / 1000)),
    }));
  }

  async simulateGame(homeTeamId: number, awayTeamId: number, weekContext?: number) {
    try {
      const response = await axios.post(`${analyticsUrl}/simulate/game`, {
        home_team_id: homeTeamId, away_team_id: awayTeamId, week: weekContext,
      }, { timeout: 60000 });
      return response.data;
    } catch {
      return this.eloFallbackPrediction(0);
    }
  }

  async getModelAccuracy() {
    const { rows } = await pool.query(`
      SELECT model_version,
        COUNT(*) as total_predictions,
        AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) as accuracy,
        AVG(absolute_error) as mae,
        COUNT(DISTINCT game_id) as games_evaluated
      FROM model_accuracy_log GROUP BY model_version ORDER BY MAX(recorded_at) DESC
    `);
    return rows;
  }

  async getPredictionLeaderboard(week?: number) {
    const w = week || getCurrentNFLWeek();
    const { rows } = await pool.query(`
      SELECT pp.*, p.full_name, p.position, t.abbreviation as team_abbr,
        pp.confidence_score * pp.matchup_rating as composite_score
      FROM player_predictions pp
      JOIN players p ON p.id = pp.player_id JOIN teams t ON t.id = p.team_id
      JOIN games g ON g.id = pp.game_id WHERE g.week = $1 AND g.season_year = $2
      ORDER BY composite_score DESC LIMIT 20
    `, [w, getCurrentNFLSeason()]);
    return rows;
  }
}
