import cron from 'node-cron';
import { pool } from '../database/connection';
import { fetchESPNTeams, fetchESPNScoreboard, fetchESPNRoster, getCurrentNFLWeek, getCurrentNFLSeason } from '../services/espnService';
import { logger } from '../config/logger';

// NFL team colors & info (ESPN IDs map to these)
const TEAM_COLORS: Record<string, { primary: string; secondary: string }> = {
  'ARI': { primary: '#97233F', secondary: '#FFB612' },
  'ATL': { primary: '#A71930', secondary: '#000000' },
  'BAL': { primary: '#241773', secondary: '#000000' },
  'BUF': { primary: '#00338D', secondary: '#C60C30' },
  'CAR': { primary: '#0085CA', secondary: '#101820' },
  'CHI': { primary: '#0B162A', secondary: '#C83803' },
  'CIN': { primary: '#FB4F14', secondary: '#000000' },
  'CLE': { primary: '#311D00', secondary: '#FF3C00' },
  'DAL': { primary: '#003594', secondary: '#041E42' },
  'DEN': { primary: '#FB4F14', secondary: '#002244' },
  'DET': { primary: '#0076B6', secondary: '#B0B7BC' },
  'GB':  { primary: '#203731', secondary: '#FFB612' },
  'HOU': { primary: '#03202F', secondary: '#A71930' },
  'IND': { primary: '#002C5F', secondary: '#A2AAAD' },
  'JAX': { primary: '#006778', secondary: '#D7A22A' },
  'KC':  { primary: '#E31837', secondary: '#FFB81C' },
  'LV':  { primary: '#000000', secondary: '#A5ACAF' },
  'LAC': { primary: '#0080C6', secondary: '#FFC20E' },
  'LA':  { primary: '#003594', secondary: '#FFA300' },
  'MIA': { primary: '#008E97', secondary: '#FC4C02' },
  'MIN': { primary: '#4F2683', secondary: '#FFC62F' },
  'NE':  { primary: '#002244', secondary: '#C60C30' },
  'NO':  { primary: '#D3BC8D', secondary: '#101820' },
  'NYG': { primary: '#0B2265', secondary: '#A71930' },
  'NYJ': { primary: '#125740', secondary: '#000000' },
  'PHI': { primary: '#004C54', secondary: '#A5ACAF' },
  'PIT': { primary: '#FFB612', secondary: '#101820' },
  'SF':  { primary: '#AA0000', secondary: '#B3995D' },
  'SEA': { primary: '#002244', secondary: '#69BE28' },
  'TB':  { primary: '#D50A0A', secondary: '#FF7900' },
  'TEN': { primary: '#0C2340', secondary: '#4B92DB' },
  'WAS': { primary: '#5A1414', secondary: '#FFB612' },
};

export async function syncTeams() {
  logger.info('Syncing teams from ESPN...');
  try {
    const teams = await fetchESPNTeams();
    for (const entry of teams) {
      const t = entry.team;
      const abbr = t.abbreviation?.toUpperCase();
      const colors = TEAM_COLORS[abbr] || { primary: '#1a1a2e', secondary: '#16213e' };
      await pool.query(`
        INSERT INTO teams (name, city, abbreviation, conference, division, home_stadium, logo_url, primary_color, secondary_color, external_id, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
        ON CONFLICT (abbreviation) DO UPDATE SET name=$1, city=$2, logo_url=$7, updated_at=NOW()
      `, [
        t.displayName, t.location, abbr,
        t.groups?.parent?.abbreviation || 'NFC',
        t.groups?.name || 'Unknown Division',
        t.venue?.fullName || '',
        t.logos?.[0]?.href || '',
        colors.primary, colors.secondary,
        String(t.id),
      ]);

      // Initialize elo rating if not exists
      await pool.query(`
        INSERT INTO elo_ratings (team_id, rating)
        SELECT id, 1500 FROM teams WHERE abbreviation = $1
        ON CONFLICT (team_id) DO NOTHING
      `, [abbr]);
    }
    logger.info(`Synced ${teams.length} teams`);
  } catch (err) {
    logger.error('Failed to sync teams', err);
  }
}

export async function syncGames(week?: number, season?: number) {
  const w = week || getCurrentNFLWeek();
  const s = season || getCurrentNFLSeason();
  logger.info(`Syncing games week ${w} season ${s}`);
  try {
    const events = await fetchESPNScoreboard(w, s);
    for (const event of events) {
      const competition = event.competitions?.[0];
      if (!competition) continue;
      const homeComp = competition.competitors.find((c: any) => c.homeAway === 'home');
      const awayComp = competition.competitors.find((c: any) => c.homeAway === 'away');
      const homeAbbr = homeComp?.team?.abbreviation?.toUpperCase();
      const awayAbbr = awayComp?.team?.abbreviation?.toUpperCase();

      const [homeTeam, awayTeam] = await Promise.all([
        pool.query('SELECT id FROM teams WHERE abbreviation = $1', [homeAbbr]),
        pool.query('SELECT id FROM teams WHERE abbreviation = $1', [awayAbbr]),
      ]);
      if (!homeTeam.rows.length || !awayTeam.rows.length) continue;

      const status = competition.status?.type?.name === 'STATUS_FINAL' ? 'final'
        : competition.status?.type?.name === 'STATUS_IN_PROGRESS' ? 'in_progress' : 'scheduled';

      await pool.query(`
        INSERT INTO games (season_year, season_type, week, game_date, home_team_id, away_team_id,
          venue, home_score, away_score, status, broadcast_network, external_game_id, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,NOW())
        ON CONFLICT (external_game_id) DO UPDATE SET
          home_score=$8, away_score=$9, status=$10, updated_at=NOW()
      `, [
        s, 'regular', w, new Date(competition.date),
        homeTeam.rows[0].id, awayTeam.rows[0].id,
        competition.venue?.fullName || '',
        status === 'scheduled' ? null : Number(homeComp?.score || 0),
        status === 'scheduled' ? null : Number(awayComp?.score || 0),
        status, competition.broadcasts?.[0]?.names?.[0] || '',
        String(event.id),
      ]);
    }
    logger.info(`Synced ${events.length} games for week ${w}`);
  } catch (err) {
    logger.error('Failed to sync games', err);
  }
}

export async function syncAllWeeks() {
  const season = getCurrentNFLSeason();
  for (let week = 1; week <= 18; week++) {
    await syncGames(week, season);
  }
}

export function startCronJobs() {
  // Sync live scores every 5 min (game days)
  cron.schedule('*/5 * * * *', () => syncGames(), { scheduled: true });

  // Full team/game sync every 2 hours
  cron.schedule('0 */2 * * *', async () => {
    await syncTeams();
    await syncAllWeeks();
  });

  // Initial sync on startup (slightly delayed)
  setTimeout(async () => {
    await syncTeams();
    await syncAllWeeks();
  }, 5000);

  logger.info('Cron jobs started');
}
