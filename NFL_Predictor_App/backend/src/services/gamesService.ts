import { pool } from '../database/connection';
import { getCurrentNFLSeason, getCurrentNFLWeek, fetchESPNScoreboard, fetchESPNGameSummary } from './espnService';

interface GameFilter { season?: number; week?: number; teamId?: number; status?: string; }

export class GamesService {
  async getGames({ season, week, teamId, status }: GameFilter) {
    const s = season || getCurrentNFLSeason();
    const conditions: string[] = ['g.season_year = $1', "g.season_type = 'regular'"];
    const params: unknown[] = [s];
    let i = 2;
    if (week) { conditions.push(`g.week = $${i++}`); params.push(week); }
    if (teamId) { conditions.push(`(g.home_team_id = $${i} OR g.away_team_id = $${i})`); params.push(teamId); i++; }
    if (status) { conditions.push(`g.status = $${i++}`); params.push(status); }
    const { rows } = await pool.query(`
      SELECT g.*, ht.name as home_team_name, ht.abbreviation as home_abbr, ht.primary_color as home_color,
        at2.name as away_team_name, at2.abbreviation as away_abbr, at2.primary_color as away_color
      FROM games g
      JOIN teams ht ON ht.id = g.home_team_id JOIN teams at2 ON at2.id = g.away_team_id
      WHERE ${conditions.join(' AND ')} ORDER BY g.week, g.game_date
    `, params);
    return rows;
  }

  async getUpcomingGames() {
    const week = getCurrentNFLWeek();
    const season = getCurrentNFLSeason();
    return this.getGames({ season, week, status: 'scheduled' });
  }

  async getLiveGames() {
    const { rows } = await pool.query(`
      SELECT g.*, ht.name as home_team_name, ht.abbreviation as home_abbr,
        at2.name as away_team_name, at2.abbreviation as away_abbr
      FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at2 ON at2.id = g.away_team_id
      WHERE g.status = 'in_progress' ORDER BY g.game_date
    `);
    return rows;
  }

  async getGameById(id: number) {
    const { rows } = await pool.query(`
      SELECT g.*, ht.name as home_team_name, ht.abbreviation as home_abbr, ht.primary_color as home_color,
        at2.name as away_team_name, at2.abbreviation as away_abbr, at2.primary_color as away_color
      FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at2 ON at2.id = g.away_team_id
      WHERE g.id = $1
    `, [id]);
    return rows[0] || null;
  }

  async getBoxScore(gameId: number) {
    const [teamStats, playerStats] = await Promise.all([
      pool.query(`
        SELECT tgs.*, t.name as team_name, t.abbreviation
        FROM team_game_stats tgs JOIN teams t ON t.id = tgs.team_id WHERE tgs.game_id = $1
      `, [gameId]),
      pool.query(`
        SELECT pgs.*, p.full_name, p.position, p.jersey_number, t.abbreviation as team_abbr
        FROM player_game_stats pgs JOIN players p ON p.id = pgs.player_id JOIN teams t ON t.id = pgs.team_id
        WHERE pgs.game_id = $1 ORDER BY t.id, p.position, pgs.snaps_played DESC
      `, [gameId]),
    ]);
    return { teamStats: teamStats.rows, playerStats: playerStats.rows };
  }

  async getPlayByPlay(gameId: number) {
    const game = await this.getGameById(gameId);
    if (!game?.external_game_id) return [];
    try {
      const summary = await fetchESPNGameSummary(game.external_game_id);
      return summary?.plays || [];
    } catch { return []; }
  }

  async getDrives(gameId: number) {
    const game = await this.getGameById(gameId);
    if (!game?.external_game_id) return [];
    try {
      const summary = await fetchESPNGameSummary(game.external_game_id);
      return summary?.drives?.previous || [];
    } catch { return []; }
  }
}
