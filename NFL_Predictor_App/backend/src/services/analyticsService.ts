import { pool } from '../database/connection';
import { getCurrentNFLSeason, getCurrentNFLWeek } from './espnService';
import axios from 'axios';

export class AnalyticsService {
  async getStandings(season?: number) {
    const s = season || getCurrentNFLSeason();
    const { rows } = await pool.query(`
      SELECT t.id, t.name, t.city, t.abbreviation, t.conference, t.division, t.primary_color,
        SUM(CASE WHEN g.status='final' AND ((g.home_team_id=t.id AND g.home_score>g.away_score) OR (g.away_team_id=t.id AND g.away_score>g.home_score)) THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN g.status='final' AND ((g.home_team_id=t.id AND g.home_score<g.away_score) OR (g.away_team_id=t.id AND g.away_score<g.home_score)) THEN 1 ELSE 0 END) as losses,
        SUM(CASE WHEN g.status='final' AND g.home_score=g.away_score THEN 1 ELSE 0 END) as ties,
        SUM(CASE WHEN g.home_team_id=t.id AND g.status='final' THEN g.home_score ELSE 0 END) +
        SUM(CASE WHEN g.away_team_id=t.id AND g.status='final' THEN g.away_score ELSE 0 END) as points_for,
        SUM(CASE WHEN g.home_team_id=t.id AND g.status='final' THEN g.away_score ELSE 0 END) +
        SUM(CASE WHEN g.away_team_id=t.id AND g.status='final' THEN g.home_score ELSE 0 END) as points_against,
        e.rating as elo_rating
      FROM teams t
      LEFT JOIN games g ON (g.home_team_id=t.id OR g.away_team_id=t.id) AND g.season_year=$1 AND g.season_type='regular'
      LEFT JOIN elo_ratings e ON e.team_id=t.id
      WHERE t.deleted_at IS NULL
      GROUP BY t.id, e.rating
      ORDER BY t.conference, t.division, wins DESC, (
        SUM(CASE WHEN g.home_team_id=t.id AND g.status='final' THEN g.home_score ELSE 0 END) +
        SUM(CASE WHEN g.away_team_id=t.id AND g.status='final' THEN g.away_score ELSE 0 END) -
        SUM(CASE WHEN g.home_team_id=t.id AND g.status='final' THEN g.away_score ELSE 0 END) -
        SUM(CASE WHEN g.away_team_id=t.id AND g.status='final' THEN g.home_score ELSE 0 END)
      ) DESC
    `, [s]);
    return rows;
  }

  async getPowerRankings(week?: number, season?: number) {
    const s = season || getCurrentNFLSeason();
    const w = week || getCurrentNFLWeek();
    const { rows } = await pool.query(`
      SELECT t.id, t.name, t.abbreviation, t.conference, t.primary_color,
        e.rating as elo,
        AVG(tgs.epa_per_play) as avg_epa,
        AVG(tgs.points_scored - tgs.points_allowed) as avg_point_diff,
        RANK() OVER (ORDER BY e.rating DESC NULLS LAST) as power_rank
      FROM teams t
      LEFT JOIN elo_ratings e ON e.team_id = t.id
      LEFT JOIN team_game_stats tgs ON tgs.team_id = t.id
      LEFT JOIN games g ON g.id = tgs.game_id AND g.season_year = $1 AND g.week <= $2
      WHERE t.deleted_at IS NULL
      GROUP BY t.id, e.rating
      ORDER BY power_rank
    `, [s, w]);
    return rows;
  }

  async getScheduleDifficulty(season?: number) {
    const s = season || getCurrentNFLSeason();
    const w = getCurrentNFLWeek();
    const { rows } = await pool.query(`
      SELECT t.id, t.name, t.abbreviation,
        AVG(opp_elo.rating) as avg_remaining_opp_elo,
        COUNT(upcoming.id) as remaining_games
      FROM teams t
      JOIN games upcoming ON (upcoming.home_team_id=t.id OR upcoming.away_team_id=t.id)
        AND upcoming.season_year=$1 AND upcoming.week > $2 AND upcoming.status='scheduled'
      JOIN elo_ratings opp_elo ON opp_elo.team_id = CASE WHEN upcoming.home_team_id=t.id THEN upcoming.away_team_id ELSE upcoming.home_team_id END
      WHERE t.deleted_at IS NULL
      GROUP BY t.id ORDER BY avg_remaining_opp_elo DESC
    `, [s, w]);
    return rows;
  }

  async getLeagueTrends(season?: number) {
    const s = season || getCurrentNFLSeason();
    const { rows } = await pool.query(`
      SELECT g.week,
        AVG(tgs.points_scored) as avg_ppg,
        AVG(tgs.passing_yards) as avg_pass_yards,
        AVG(tgs.rushing_yards) as avg_rush_yards,
        AVG(CASE WHEN tgs.plays_run > 0 THEN tgs.passing_yards::float / (tgs.plays_run) ELSE 0 END) as pass_rate
      FROM team_game_stats tgs JOIN games g ON g.id = tgs.game_id
      WHERE g.season_year = $1 AND g.status = 'final'
      GROUP BY g.week ORDER BY g.week
    `, [s]);
    return rows;
  }

  async getMatchupAnalysis(gameId: number) {
    const { rows } = await pool.query(
      'SELECT * FROM games WHERE id = $1', [gameId]
    );
    if (!rows.length) return null;
    const game = rows[0];
    const [homeStats, awayStats] = await Promise.all([
      this.getTeamRecentStats(game.home_team_id),
      this.getTeamRecentStats(game.away_team_id),
    ]);
    return { game, homeStats, awayStats };
  }

  private async getTeamRecentStats(teamId: number) {
    const { rows } = await pool.query(`
      SELECT AVG(tgs.points_scored) as ppg, AVG(tgs.passing_yards) as pass_ypg,
        AVG(tgs.rushing_yards) as rush_ypg, AVG(tgs.epa_per_play) as epa
      FROM team_game_stats tgs JOIN games g ON g.id = tgs.game_id
      WHERE tgs.team_id = $1 AND g.status = 'final' ORDER BY g.week DESC LIMIT 4
    `, [teamId]);
    return rows[0];
  }

  async getWeatherImpact(week?: number) {
    const w = week || getCurrentNFLWeek();
    const s = getCurrentNFLSeason();
    const { rows } = await pool.query(`
      SELECT g.id, g.venue, g.weather_temp_f, g.weather_wind_mph, g.weather_conditions,
        ht.name as home_team, at2.name as away_team
      FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at2 ON at2.id = g.away_team_id
      WHERE g.week = $1 AND g.season_year = $2 AND g.status = 'scheduled'
        AND (g.weather_wind_mph > 15 OR g.weather_temp_f < 35 OR g.weather_conditions ILIKE '%rain%snow%')
    `, [w, s]);
    return rows;
  }

  async getOfficialsData(week?: number, season?: number) {
    // Placeholder — officials data would come from a dedicated source
    return { message: 'Officials data requires MySportsFeeds or similar source', week, season };
  }
}
