import { pool } from '../database/connection';
import { getCurrentNFLSeason } from './espnService';

export class TeamsService {
  private season(s?: number) { return s || getCurrentNFLSeason(); }

  async getAllTeams(season?: number) {
    const s = this.season(season);
    const { rows } = await pool.query(`
      SELECT t.*,
        COUNT(CASE WHEN g.home_score > g.away_score AND g.home_team_id = t.id AND g.status = 'final' THEN 1
                   WHEN g.away_score > g.home_score AND g.away_team_id = t.id AND g.status = 'final' THEN 1 END) as wins,
        COUNT(CASE WHEN g.home_score < g.away_score AND g.home_team_id = t.id AND g.status = 'final' THEN 1
                   WHEN g.away_score < g.home_score AND g.away_team_id = t.id AND g.status = 'final' THEN 1 END) as losses,
        e.rating as elo_rating
      FROM teams t
      LEFT JOIN games g ON (g.home_team_id = t.id OR g.away_team_id = t.id) AND g.season_year = $1 AND g.season_type = 'regular'
      LEFT JOIN elo_ratings e ON e.team_id = t.id
      WHERE t.deleted_at IS NULL
      GROUP BY t.id, e.rating
      ORDER BY t.conference, t.division, t.name
    `, [s]);
    return rows;
  }

  async getTeamById(id: number) {
    const { rows } = await pool.query('SELECT * FROM teams WHERE id = $1 AND deleted_at IS NULL', [id]);
    return rows[0] || null;
  }

  async getTeamStats(teamId: number, season?: number) {
    const s = this.season(season);
    const { rows } = await pool.query(`
      SELECT
        AVG(tgs.points_scored) as ppg,
        AVG(tgs.points_allowed) as ppg_allowed,
        AVG(tgs.total_yards) as yards_per_game,
        AVG(tgs.passing_yards) as pass_yards_per_game,
        AVG(tgs.rushing_yards) as rush_yards_per_game,
        SUM(tgs.turnovers) as total_turnovers,
        SUM(tgs.interceptions_caught) as interceptions,
        AVG(CASE WHEN tgs.third_down_attempts > 0 THEN tgs.third_down_conversions::float / tgs.third_down_attempts ELSE 0 END) as third_down_pct,
        AVG(tgs.yards_per_play) as yards_per_play,
        AVG(tgs.epa_per_play) as epa_per_play,
        AVG(tgs.completion_percentage) as completion_pct,
        AVG(tgs.sacks) as sacks_per_game,
        COUNT(*) as games_played
      FROM team_game_stats tgs
      JOIN games g ON g.id = tgs.game_id
      WHERE tgs.team_id = $1 AND g.season_year = $2 AND g.season_type = 'regular' AND g.status = 'final'
    `, [teamId, s]);
    return rows[0];
  }

  async getTeamWeeklyStats(teamId: number, season?: number) {
    const s = this.season(season);
    const { rows } = await pool.query(`
      SELECT g.week, tgs.*, g.home_team_id, g.away_team_id, g.home_score, g.away_score,
        CASE WHEN tgs.team_id = g.home_team_id THEN at2.abbreviation ELSE ht.abbreviation END as opponent_abbr
      FROM team_game_stats tgs
      JOIN games g ON g.id = tgs.game_id
      JOIN teams ht ON ht.id = g.home_team_id
      JOIN teams at2 ON at2.id = g.away_team_id
      WHERE tgs.team_id = $1 AND g.season_year = $2 AND g.season_type = 'regular'
      ORDER BY g.week
    `, [teamId, s]);
    return rows;
  }

  async getTeamRoster(teamId: number) {
    const { rows } = await pool.query(`
      SELECT * FROM players WHERE team_id = $1 AND deleted_at IS NULL ORDER BY position, depth_chart_position, full_name
    `, [teamId]);
    return rows;
  }

  async getTeamSchedule(teamId: number, season?: number) {
    const s = this.season(season);
    const { rows } = await pool.query(`
      SELECT g.*, ht.name as home_team_name, ht.abbreviation as home_abbr, ht.primary_color as home_color,
        at2.name as away_team_name, at2.abbreviation as away_abbr, at2.primary_color as away_color
      FROM games g
      JOIN teams ht ON ht.id = g.home_team_id
      JOIN teams at2 ON at2.id = g.away_team_id
      WHERE (g.home_team_id = $1 OR g.away_team_id = $1) AND g.season_year = $2
      ORDER BY g.week
    `, [teamId, s]);
    return rows;
  }

  async getTeamSplits(teamId: number, season?: number) {
    const s = this.season(season);
    const { rows } = await pool.query(`
      SELECT
        AVG(CASE WHEN tgs.is_home THEN tgs.points_scored END) as home_ppg,
        AVG(CASE WHEN NOT tgs.is_home THEN tgs.points_scored END) as away_ppg,
        AVG(CASE WHEN tgs.is_home THEN tgs.total_yards END) as home_yards,
        AVG(CASE WHEN NOT tgs.is_home THEN tgs.total_yards END) as away_yards,
        COUNT(CASE WHEN tgs.is_home AND tgs.points_scored > tgs.points_allowed THEN 1 END) as home_wins,
        COUNT(CASE WHEN NOT tgs.is_home AND tgs.points_scored > tgs.points_allowed THEN 1 END) as away_wins
      FROM team_game_stats tgs
      JOIN games g ON g.id = tgs.game_id
      WHERE tgs.team_id = $1 AND g.season_year = $2 AND g.status = 'final'
    `, [teamId, s]);
    return rows[0];
  }

  async getTeamSituational(teamId: number, season?: number) {
    const s = this.season(season);
    const { rows } = await pool.query(`
      SELECT
        SUM(tgs.red_zone_trips) as total_rz_trips,
        SUM(tgs.red_zone_touchdowns) as total_rz_tds,
        AVG(CASE WHEN tgs.red_zone_trips > 0 THEN tgs.red_zone_touchdowns::float / tgs.red_zone_trips ELSE 0 END) as rz_td_pct,
        AVG(CASE WHEN tgs.third_down_attempts > 0 THEN tgs.third_down_conversions::float / tgs.third_down_attempts ELSE 0 END) as third_down_pct,
        AVG(CASE WHEN tgs.fourth_down_attempts > 0 THEN tgs.fourth_down_conversions::float / tgs.fourth_down_attempts ELSE 0 END) as fourth_down_pct
      FROM team_game_stats tgs
      JOIN games g ON g.id = tgs.game_id
      WHERE tgs.team_id = $1 AND g.season_year = $2 AND g.season_type = 'regular'
    `, [teamId, s]);
    return rows[0];
  }

  async getTeamAdvanced(teamId: number, season?: number) {
    const s = this.season(season);
    const { rows } = await pool.query(`
      SELECT
        AVG(tgs.epa_per_play) as avg_epa_per_play,
        AVG(tgs.success_rate) as avg_success_rate,
        AVG(tgs.blitz_rate) as avg_blitz_rate,
        AVG(tgs.pressure_rate) as avg_pressure_rate,
        e.rating as elo_rating
      FROM team_game_stats tgs
      JOIN games g ON g.id = tgs.game_id
      LEFT JOIN elo_ratings e ON e.team_id = tgs.team_id
      WHERE tgs.team_id = $1 AND g.season_year = $2
      GROUP BY e.rating
    `, [teamId, s]);
    return rows[0];
  }

  async getTeamInjuries(teamId: number) {
    const { rows } = await pool.query(`
      SELECT * FROM players WHERE team_id = $1 AND injury_status != 'Active' AND deleted_at IS NULL ORDER BY full_name
    `, [teamId]);
    return rows;
  }

  async compareTeams(ids: number[]) {
    if (!ids.length) return [];
    const placeholders = ids.map((_, i) => `$${i + 1}`).join(',');
    const { rows } = await pool.query(`SELECT * FROM teams WHERE id IN (${placeholders})`, ids);
    return rows;
  }
}
