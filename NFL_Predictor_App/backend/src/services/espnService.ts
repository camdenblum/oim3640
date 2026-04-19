import axios from 'axios';
import { logger } from '../config/logger';

const ESPN_BASE = process.env.ESPN_BASE_URL || 'https://site.api.espn.com/apis/site/v2/sports/football/nfl';

const espn = axios.create({ baseURL: ESPN_BASE, timeout: 10000 });

export async function fetchESPNTeams() {
  const res = await espn.get('/teams?limit=32');
  return res.data?.sports?.[0]?.leagues?.[0]?.teams || [];
}

export async function fetchESPNScoreboard(week: number, season?: number, seasonType = 2) {
  const params: Record<string, unknown> = { week, seasontype: seasonType };
  if (season) params.season = season;
  const res = await espn.get('/scoreboard', { params });
  return res.data?.events || [];
}

export async function fetchESPNGameSummary(gameId: string) {
  const res = await espn.get(`/summary`, { params: { event: gameId } });
  return res.data;
}

export async function fetchESPNRoster(teamId: string) {
  const res = await espn.get(`/teams/${teamId}/roster`);
  return res.data?.athletes || [];
}

export async function fetchESPNSchedule(teamId: string, season?: number) {
  const params: Record<string, unknown> = {};
  if (season) params.season = season;
  const res = await espn.get(`/teams/${teamId}/schedule`, { params });
  return res.data?.events || [];
}

export async function fetchESPNInjuries() {
  try {
    const res = await espn.get('/injuries');
    return res.data?.injuries || [];
  } catch (err) {
    logger.warn('Could not fetch ESPN injuries', err);
    return [];
  }
}

export function getCurrentNFLWeek(): number {
  const now = new Date();
  const seasonStart = new Date(now.getFullYear(), 8, 5); // approx Sept 5
  if (now < seasonStart) return 1;
  const diff = Math.floor((now.getTime() - seasonStart.getTime()) / (7 * 24 * 60 * 60 * 1000));
  return Math.min(Math.max(diff + 1, 1), 18);
}

export function getCurrentNFLSeason(): number {
  const now = new Date();
  return now.getMonth() >= 8 ? now.getFullYear() : now.getFullYear() - 1;
}
