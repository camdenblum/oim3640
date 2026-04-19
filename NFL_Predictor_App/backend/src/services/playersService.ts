import { pool } from '../database/connection';
import { getCurrentNFLSeason } from './espnService';

interface PlayerFilter { teamId?: number; position?: string; status?: string; page: number; limit: number; }

export class PlayersService {
  async getPlayers({ teamId, position, status, page, limit }: PlayerFilter) {
    const conditions: string[] = ['p.deleted_at IS NULL'];
    const params: unknown[] = [];
    let i = 1;
    if (teamId) { conditions.push(`p.team_id = $${i++}`); params.push(teamId); }
    if (position) { conditions.push(`p.position = $${i++}`); params.push(position.toUpperCase()); }
    if (status) { conditions.push(`p.injury_status = $${i++}`); params.push(status); }
    const offset = (page - 1) * limit;
    const where = conditions.join(' AND ');
    params.push(limit, offset);
    const { rows } = await pool.query(`
      SELECT p.*, t.name as team_name, t.abbreviation as team_abbr, t.primary_color
      FROM players p LEFT JOIN teams t ON t.id = p.team_id
      WHERE ${where} ORDER BY p.full_name LIMIT $${i++} OFFSET $${i}
    `, params);
    return rows;
  }

  async searchPlayers(query: string) {
    const { rows } = await pool.query(`
      SELECT p.*, t.abbreviation as team_abbr FROM players p
      LEFT JOIN teams t ON t.id = p.team_id
      WHERE p.deleted_at IS NULL AND (p.full_name ILIKE $1 OR p.position ILIKE $1)
      ORDER BY p.full_name LIMIT 20
    `, [`%${query}%`]);
    return rows;
  }

  async getPlayerById(id: number) {
    const { rows } = await pool.query(`
      SELECT p.*, t.name as team_name, t.abbreviation as team_abbr, t.primary_color, t.secondary_color
      FROM players p LEFT JOIN teams t ON t.id = p.team_id WHERE p.id = $1
    `, [id]);
    return rows[0] || null;
  }

  async getPlayerStats(playerId: number, season?: number) {
    const s = season || getCurrentNFLSeason();
    const { rows } = await pool.query(`
      SELECT
        SUM(pgs.qb_yards) as total_pass_yards, SUM(pgs.qb_touchdowns) as total_pass_tds,
        SUM(pgs.qb_interceptions) as total_ints, AVG(pgs.qb_rating) as avg_qb_rating,
        SUM(pgs.rb_yards) as total_rush_yards, SUM(pgs.rb_touchdowns) as total_rush_tds,
        SUM(pgs.rb_carries) as total_carries,
        SUM(pgs.rec_yards) as total_rec_yards, SUM(pgs.rec_touchdowns) as total_rec_tds,
        SUM(pgs.rec_receptions) as total_receptions, SUM(pgs.rec_targets) as total_targets,
        SUM(pgs.def_sacks) as total_sacks, SUM(pgs.def_tackles) as total_tackles,
        SUM(pgs.def_interceptions) as total_def_ints,
        SUM(COALESCE(pgs.qb_fantasy_points,0) + COALESCE(pgs.rb_fantasy_points,0) +
            COALESCE(pgs.rec_fantasy_points,0) + COALESCE(pgs.def_fantasy_points,0)) as total_fantasy_pts,
        COUNT(*) as games_played
      FROM player_game_stats pgs
      JOIN games g ON g.id = pgs.game_id
      WHERE pgs.player_id = $1 AND g.season_year = $2 AND g.status = 'final'
    `, [playerId, s]);
    return rows[0];
  }

  async getPlayerGameLog(playerId: number, season?: number) {
    const s = season || getCurrentNFLSeason();
    const { rows } = await pool.query(`
      SELECT pgs.*, g.week, g.game_date, g.home_score, g.away_score,
        ht.abbreviation as home_abbr, at2.abbreviation as away_abbr,
        opp.abbreviation as opponent_abbr
      FROM player_game_stats pgs
      JOIN games g ON g.id = pgs.game_id
      JOIN teams ht ON ht.id = g.home_team_id
      JOIN teams at2 ON at2.id = g.away_team_id
      LEFT JOIN teams opp ON opp.id = pgs.opponent_team_id
      WHERE pgs.player_id = $1 AND g.season_year = $2
      ORDER BY g.week DESC
    `, [playerId, s]);
    return rows;
  }

  async getPlayerTrends(playerId: number) {
    const { rows } = await pool.query(`
      SELECT pgs.*, g.week,
        AVG(COALESCE(pgs.qb_yards,0)+COALESCE(pgs.rb_yards,0)+COALESCE(pgs.rec_yards,0))
          OVER (ORDER BY g.week ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as rolling_3_yards
      FROM player_game_stats pgs
      JOIN games g ON g.id = pgs.game_id
      WHERE pgs.player_id = $1 AND g.status = 'final'
      ORDER BY g.season_year DESC, g.week DESC LIMIT 16
    `, [playerId]);
    return rows;
  }

  async getPlayerSplits(playerId: number, season?: number) {
    const s = season || getCurrentNFLSeason();
    const { rows } = await pool.query(`
      SELECT
        AVG(CASE WHEN pgs.team_id = g.home_team_id THEN COALESCE(pgs.qb_yards,pgs.rb_yards,pgs.rec_yards) END) as home_yards,
        AVG(CASE WHEN pgs.team_id = g.away_team_id THEN COALESCE(pgs.qb_yards,pgs.rb_yards,pgs.rec_yards) END) as away_yards
      FROM player_game_stats pgs
      JOIN games g ON g.id = pgs.game_id
      WHERE pgs.player_id = $1 AND g.season_year = $2 AND g.status = 'final'
    `, [playerId, s]);
    return rows[0];
  }

  async getPlayerAdvanced(playerId: number) {
    const { rows } = await pool.query(`
      SELECT p.*, AVG(pgs.snap_percentage) as avg_snap_pct,
        AVG(pgs.rec_air_yards) as avg_air_yards, AVG(pgs.rec_yards_after_catch) as avg_yac
      FROM players p
      LEFT JOIN player_game_stats pgs ON pgs.player_id = p.id
      WHERE p.id = $1 GROUP BY p.id
    `, [playerId]);
    return rows[0];
  }

  async getPlayerSnapCounts(playerId: number, season?: number) {
    const s = season || getCurrentNFLSeason();
    const { rows } = await pool.query(`
      SELECT pgs.snaps_played, pgs.snap_percentage, g.week
      FROM player_game_stats pgs JOIN games g ON g.id = pgs.game_id
      WHERE pgs.player_id = $1 AND g.season_year = $2 ORDER BY g.week
    `, [playerId, s]);
    return rows;
  }

  async getPlayerMatchupHistory(playerId: number, opponentId?: number) {
    const params: unknown[] = [playerId];
    let where = 'pgs.player_id = $1 AND g.status = \'final\'';
    if (opponentId) { where += ' AND pgs.opponent_team_id = $2'; params.push(opponentId); }
    const { rows } = await pool.query(`
      SELECT pgs.*, g.week, g.season_year, opp.abbreviation as opponent_abbr
      FROM player_game_stats pgs JOIN games g ON g.id = pgs.game_id
      LEFT JOIN teams opp ON opp.id = pgs.opponent_team_id
      WHERE ${where} ORDER BY g.season_year DESC, g.week DESC LIMIT 20
    `, params);
    return rows;
  }

  async getLeaderboards(stat: string, position: string, season?: number, week?: number) {
    const s = season || getCurrentNFLSeason();
    const validStats: Record<string, string> = {
      qb_yards: 'SUM(pgs.qb_yards)', qb_tds: 'SUM(pgs.qb_touchdowns)',
      rb_yards: 'SUM(pgs.rb_yards)', rb_tds: 'SUM(pgs.rb_touchdowns)',
      rec_yards: 'SUM(pgs.rec_yards)', rec_tds: 'SUM(pgs.rec_touchdowns)',
      receptions: 'SUM(pgs.rec_receptions)', sacks: 'SUM(pgs.def_sacks)',
    };
    const statExpr = validStats[stat] || 'SUM(pgs.qb_yards)';
    const params: unknown[] = [s, position.toUpperCase()];
    let weekClause = '';
    if (week) { weekClause = 'AND g.week = $3'; params.push(week); }
    const { rows } = await pool.query(`
      SELECT p.id, p.full_name, p.position, t.abbreviation as team_abbr,
        ${statExpr} as stat_value
      FROM players p
      JOIN player_game_stats pgs ON pgs.player_id = p.id
      JOIN games g ON g.id = pgs.game_id
      JOIN teams t ON t.id = p.team_id
      WHERE g.season_year = $1 AND p.position = $2 AND g.status = 'final' ${weekClause}
      GROUP BY p.id, p.full_name, p.position, t.abbreviation
      ORDER BY stat_value DESC NULLS LAST LIMIT 25
    `, params);
    return rows;
  }
}
