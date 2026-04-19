import { Pool } from 'pg';
import { logger } from '../config/logger';

export const pool = new Pool({ connectionString: process.env.DATABASE_URL });

export async function initDatabase() {
  const client = await pool.connect();
  try {
    await client.query('SELECT 1');
    logger.info('Database connected');
    await runMigrations(client);
  } finally {
    client.release();
  }
}

async function runMigrations(client: any) {
  await client.query(`
    CREATE TABLE IF NOT EXISTS migrations (
      id SERIAL PRIMARY KEY,
      name VARCHAR(255) UNIQUE NOT NULL,
      run_at TIMESTAMP DEFAULT NOW()
    )
  `);

  const migrations = [
    { name: '001_create_teams', sql: CREATE_TEAMS_SQL },
    { name: '002_create_players', sql: CREATE_PLAYERS_SQL },
    { name: '003_create_games', sql: CREATE_GAMES_SQL },
    { name: '004_create_team_game_stats', sql: CREATE_TEAM_GAME_STATS_SQL },
    { name: '005_create_player_game_stats', sql: CREATE_PLAYER_GAME_STATS_SQL },
    { name: '006_create_predictions', sql: CREATE_PREDICTIONS_SQL },
    { name: '007_create_model_accuracy_log', sql: CREATE_MODEL_ACCURACY_LOG_SQL },
    { name: '008_create_elo_ratings', sql: CREATE_ELO_RATINGS_SQL },
    { name: '009_create_users', sql: CREATE_USERS_SQL },
  ];

  for (const migration of migrations) {
    const exists = await client.query('SELECT id FROM migrations WHERE name = $1', [migration.name]);
    if (exists.rows.length === 0) {
      await client.query(migration.sql);
      await client.query('INSERT INTO migrations (name) VALUES ($1)', [migration.name]);
      logger.info(`Migration ${migration.name} applied`);
    }
  }
}

const CREATE_TEAMS_SQL = `
CREATE TABLE IF NOT EXISTS teams (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  city VARCHAR(100),
  abbreviation VARCHAR(5) UNIQUE,
  conference VARCHAR(10),
  division VARCHAR(20),
  home_stadium VARCHAR(100),
  head_coach VARCHAR(100),
  offensive_coordinator VARCHAR(100),
  defensive_coordinator VARCHAR(100),
  logo_url TEXT,
  primary_color VARCHAR(7),
  secondary_color VARCHAR(7),
  external_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP
)`;

const CREATE_PLAYERS_SQL = `
CREATE TABLE IF NOT EXISTS players (
  id SERIAL PRIMARY KEY,
  team_id INTEGER REFERENCES teams(id),
  full_name VARCHAR(150),
  position VARCHAR(10),
  jersey_number INTEGER,
  age INTEGER,
  height_inches INTEGER,
  weight_lbs INTEGER,
  years_experience INTEGER,
  college VARCHAR(100),
  draft_year INTEGER,
  draft_round INTEGER,
  draft_pick INTEGER,
  injury_status VARCHAR(30) DEFAULT 'Active',
  injury_description TEXT,
  contract_years_remaining INTEGER,
  contract_aav_millions DECIMAL(6,2),
  is_starter BOOLEAN DEFAULT false,
  depth_chart_position INTEGER,
  external_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP
)`;

const CREATE_GAMES_SQL = `
CREATE TABLE IF NOT EXISTS games (
  id SERIAL PRIMARY KEY,
  season_year INTEGER,
  season_type VARCHAR(20) DEFAULT 'regular',
  week INTEGER,
  game_date TIMESTAMP,
  home_team_id INTEGER REFERENCES teams(id),
  away_team_id INTEGER REFERENCES teams(id),
  venue VARCHAR(100),
  surface VARCHAR(30),
  weather_temp_f INTEGER,
  weather_wind_mph INTEGER,
  weather_conditions VARCHAR(100),
  home_score INTEGER,
  away_score INTEGER,
  overtime BOOLEAN DEFAULT false,
  status VARCHAR(20) DEFAULT 'scheduled',
  broadcast_network VARCHAR(20),
  external_game_id VARCHAR(50) UNIQUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_games_season_week ON games(season_year, week);
CREATE INDEX IF NOT EXISTS idx_games_status ON games(status);`;

const CREATE_TEAM_GAME_STATS_SQL = `
CREATE TABLE IF NOT EXISTS team_game_stats (
  id SERIAL PRIMARY KEY,
  game_id INTEGER REFERENCES games(id),
  team_id INTEGER REFERENCES teams(id),
  is_home BOOLEAN,
  points_scored INTEGER DEFAULT 0,
  points_allowed INTEGER DEFAULT 0,
  total_yards INTEGER DEFAULT 0,
  passing_yards INTEGER DEFAULT 0,
  rushing_yards INTEGER DEFAULT 0,
  first_downs INTEGER DEFAULT 0,
  third_down_conversions INTEGER DEFAULT 0,
  third_down_attempts INTEGER DEFAULT 0,
  fourth_down_conversions INTEGER DEFAULT 0,
  fourth_down_attempts INTEGER DEFAULT 0,
  red_zone_trips INTEGER DEFAULT 0,
  red_zone_touchdowns INTEGER DEFAULT 0,
  time_of_possession_seconds INTEGER DEFAULT 0,
  plays_run INTEGER DEFAULT 0,
  yards_per_play DECIMAL(4,2),
  completions INTEGER DEFAULT 0,
  pass_attempts INTEGER DEFAULT 0,
  completion_percentage DECIMAL(5,2),
  passing_touchdowns INTEGER DEFAULT 0,
  interceptions_thrown INTEGER DEFAULT 0,
  times_sacked INTEGER DEFAULT 0,
  sack_yards_lost INTEGER DEFAULT 0,
  qb_rating DECIMAL(6,2),
  rushing_attempts INTEGER DEFAULT 0,
  rushing_touchdowns INTEGER DEFAULT 0,
  yards_per_carry DECIMAL(4,2),
  sacks DECIMAL(4,1) DEFAULT 0,
  tackles_for_loss DECIMAL(4,1) DEFAULT 0,
  interceptions_caught INTEGER DEFAULT 0,
  fumbles_recovered INTEGER DEFAULT 0,
  turnovers INTEGER DEFAULT 0,
  fumbles_lost INTEGER DEFAULT 0,
  penalties INTEGER DEFAULT 0,
  penalty_yards INTEGER DEFAULT 0,
  blitz_rate DECIMAL(4,2),
  pressure_rate DECIMAL(4,2),
  epa_per_play DECIMAL(6,4),
  success_rate DECIMAL(5,4),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_team_game_stats_game ON team_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_team_game_stats_team ON team_game_stats(team_id);`;

const CREATE_PLAYER_GAME_STATS_SQL = `
CREATE TABLE IF NOT EXISTS player_game_stats (
  id SERIAL PRIMARY KEY,
  game_id INTEGER REFERENCES games(id),
  player_id INTEGER REFERENCES players(id),
  team_id INTEGER REFERENCES teams(id),
  opponent_team_id INTEGER REFERENCES teams(id),
  snaps_played INTEGER DEFAULT 0,
  snap_percentage DECIMAL(5,2),
  was_starter BOOLEAN DEFAULT false,
  qb_completions INTEGER, qb_attempts INTEGER, qb_yards INTEGER,
  qb_touchdowns INTEGER, qb_interceptions INTEGER, qb_rating DECIMAL(6,2),
  qb_sacks_taken INTEGER, qb_air_yards INTEGER, qb_fantasy_points DECIMAL(6,2),
  rb_carries INTEGER, rb_yards INTEGER, rb_touchdowns INTEGER,
  rb_yards_per_carry DECIMAL(4,2), rb_targets INTEGER, rb_receptions INTEGER,
  rb_receiving_yards INTEGER, rb_receiving_tds INTEGER, rb_fantasy_points DECIMAL(6,2),
  rec_targets INTEGER, rec_receptions INTEGER, rec_yards INTEGER,
  rec_touchdowns INTEGER, rec_air_yards INTEGER, rec_yards_after_catch INTEGER,
  rec_fantasy_points DECIMAL(6,2),
  def_tackles DECIMAL(4,1), def_sacks DECIMAL(4,1), def_tackles_for_loss DECIMAL(4,1),
  def_interceptions INTEGER, def_pass_deflections INTEGER, def_forced_fumbles INTEGER,
  def_fantasy_points DECIMAL(6,2),
  k_fg_made INTEGER, k_fg_attempted INTEGER, k_fg_long INTEGER,
  k_xp_made INTEGER, k_xp_attempted INTEGER, k_fantasy_points DECIMAL(6,2),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_game ON player_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_player_game_stats_player ON player_game_stats(player_id);`;

const CREATE_PREDICTIONS_SQL = `
CREATE TABLE IF NOT EXISTS game_predictions (
  id SERIAL PRIMARY KEY,
  game_id INTEGER REFERENCES games(id),
  model_version VARCHAR(20),
  predicted_at TIMESTAMP DEFAULT NOW(),
  home_win_probability DECIMAL(5,4),
  away_win_probability DECIMAL(5,4),
  predicted_home_score DECIMAL(5,2),
  predicted_away_score DECIMAL(5,2),
  predicted_total_points DECIMAL(5,2),
  predicted_spread DECIMAL(5,2),
  confidence_score DECIMAL(5,4),
  key_factors JSONB,
  model_inputs JSONB,
  simulation_distribution JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS player_predictions (
  id SERIAL PRIMARY KEY,
  game_id INTEGER REFERENCES games(id),
  player_id INTEGER REFERENCES players(id),
  model_version VARCHAR(20),
  predicted_at TIMESTAMP DEFAULT NOW(),
  predicted_stats JSONB,
  confidence_score DECIMAL(5,4),
  matchup_rating DECIMAL(5,2),
  key_factors JSONB,
  floor_stats JSONB,
  ceiling_stats JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_predictions_game ON game_predictions(game_id);`;

const CREATE_MODEL_ACCURACY_LOG_SQL = `
CREATE TABLE IF NOT EXISTS model_accuracy_log (
  id SERIAL PRIMARY KEY,
  model_version VARCHAR(20),
  game_id INTEGER REFERENCES games(id),
  prediction_type VARCHAR(30),
  predicted_value DECIMAL(8,4),
  actual_value DECIMAL(8,4),
  absolute_error DECIMAL(8,4),
  was_correct BOOLEAN,
  recorded_at TIMESTAMP DEFAULT NOW()
)`;

const CREATE_ELO_RATINGS_SQL = `
CREATE TABLE IF NOT EXISTS elo_ratings (
  id SERIAL PRIMARY KEY,
  team_id INTEGER REFERENCES teams(id) UNIQUE,
  rating DECIMAL(8,2) DEFAULT 1500,
  games_played INTEGER DEFAULT 0,
  updated_at TIMESTAMP DEFAULT NOW()
)`;

const CREATE_USERS_SQL = `
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(150),
  role VARCHAR(20) DEFAULT 'viewer',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
)`;
