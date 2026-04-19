#!/usr/bin/env python3
"""
Seed script — loads historical NFL data from NFLverse into the database.
Run once after the database is initialized:
  python database/seeds/seed.py

Requires: pip install nfl-data-py psycopg2-binary python-dotenv pandas
"""
import os
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'analytics'))

import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / '.env.example')

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://nfl_user:nfl_password@localhost:5432/nfl_predictor')
SEED_YEARS = [2022, 2023, 2024]


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def run_sql_file(conn, path: str):
    with open(path) as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"Ran {path}")


def seed_teams(conn):
    sql_path = Path(__file__).parent / 'seed_teams.sql'
    run_sql_file(conn, str(sql_path))
    print("Teams seeded")


def seed_schedules(conn):
    try:
        import nfl_data_py as nfl
        print(f"Downloading schedules for {SEED_YEARS}...")
        schedules = nfl.import_schedules(SEED_YEARS)
    except Exception as e:
        print(f"Could not load NFLverse schedules: {e}")
        return

    with conn.cursor() as cur:
        for _, row in schedules.iterrows():
            try:
                # Look up team IDs
                cur.execute("SELECT id FROM teams WHERE abbreviation = %s", [str(row.get('home_team', '')).upper()])
                home_r = cur.fetchone()
                cur.execute("SELECT id FROM teams WHERE abbreviation = %s", [str(row.get('away_team', '')).upper()])
                away_r = cur.fetchone()
                if not home_r or not away_r:
                    continue

                game_date = row.get('gameday') or row.get('game_date')
                home_score = row.get('home_score')
                away_score = row.get('away_score')
                status = 'final' if pd.notna(home_score) and pd.notna(away_score) else 'scheduled'
                ext_id = str(row.get('game_id', ''))

                cur.execute("""
                    INSERT INTO games (season_year, season_type, week, game_date, home_team_id, away_team_id,
                        venue, home_score, away_score, status, external_game_id, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (external_game_id) DO UPDATE SET
                        home_score = EXCLUDED.home_score,
                        away_score = EXCLUDED.away_score,
                        status = EXCLUDED.status,
                        updated_at = NOW()
                """, [
                    int(row.get('season', 2024)),
                    str(row.get('game_type', 'REG')).lower().replace('reg', 'regular').replace('post', 'postseason'),
                    int(row.get('week', 1)),
                    game_date,
                    home_r[0], away_r[0],
                    str(row.get('stadium', '')),
                    int(home_score) if pd.notna(home_score) else None,
                    int(away_score) if pd.notna(away_score) else None,
                    status,
                    ext_id,
                ])
            except Exception as e:
                pass  # Skip problematic rows

    conn.commit()
    print(f"Schedules seeded: {len(schedules)} rows")


def seed_weekly_player_stats(conn):
    try:
        import nfl_data_py as nfl
        print(f"Downloading weekly player stats for {SEED_YEARS}...")
        weekly = nfl.import_weekly_data(SEED_YEARS)
    except Exception as e:
        print(f"Could not load weekly player data: {e}")
        return

    with conn.cursor() as cur:
        for _, row in weekly.iterrows():
            try:
                player_name = str(row.get('player_display_name', row.get('player_name', '')))
                position = str(row.get('position', 'WR')).upper()
                team_abbr = str(row.get('recent_team', '')).upper()
                season = int(row.get('season', 2024))
                week = int(row.get('week', 1))

                # Upsert player
                cur.execute("""
                    SELECT id FROM teams WHERE abbreviation = %s
                """, [team_abbr])
                team_r = cur.fetchone()

                cur.execute("""
                    INSERT INTO players (full_name, position, team_id, external_id, updated_at)
                    SELECT %s, %s, %s, %s, NOW()
                    WHERE NOT EXISTS (SELECT 1 FROM players WHERE external_id = %s)
                    RETURNING id
                """, [player_name, position, team_r[0] if team_r else None,
                      str(row.get('player_id', '')), str(row.get('player_id', ''))])
                p_row = cur.fetchone()
                if not p_row:
                    cur.execute("SELECT id FROM players WHERE external_id = %s", [str(row.get('player_id', ''))])
                    p_row = cur.fetchone()
                if not p_row:
                    continue
                player_id = p_row[0]

                # Find game
                cur.execute("""
                    SELECT g.id, g.home_team_id FROM games g
                    JOIN teams ht ON ht.id = g.home_team_id
                    JOIN teams at2 ON at2.id = g.away_team_id
                    WHERE g.season_year = %s AND g.week = %s
                      AND (ht.abbreviation = %s OR at2.abbreviation = %s)
                    LIMIT 1
                """, [season, week, team_abbr, team_abbr])
                game_r = cur.fetchone()
                if not game_r:
                    continue
                game_id = game_r[0]

                # Upsert player game stats
                attempts = row.get('attempts', 0) or 0
                completions = row.get('completions', 0) or 0
                pass_yards = row.get('passing_yards', 0) or 0
                pass_tds = row.get('passing_tds', 0) or 0
                interceptions = row.get('interceptions', 0) or 0
                carries = row.get('carries', 0) or 0
                rush_yards = row.get('rushing_yards', 0) or 0
                rush_tds = row.get('rushing_tds', 0) or 0
                targets = row.get('targets', 0) or 0
                receptions = row.get('receptions', 0) or 0
                rec_yards = row.get('receiving_yards', 0) or 0
                rec_tds = row.get('receiving_tds', 0) or 0

                cur.execute("""
                    INSERT INTO player_game_stats (game_id, player_id, team_id,
                        qb_completions, qb_attempts, qb_yards, qb_touchdowns, qb_interceptions,
                        rb_carries, rb_yards, rb_touchdowns,
                        rec_targets, rec_receptions, rec_yards, rec_touchdowns,
                        updated_at)
                    SELECT %s, %s, t.id, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                    FROM teams t WHERE t.abbreviation = %s
                    ON CONFLICT DO NOTHING
                """, [game_id, player_id, completions, attempts, pass_yards, pass_tds, interceptions,
                      carries, rush_yards, rush_tds, targets, receptions, rec_yards, rec_tds, team_abbr])

            except Exception:
                pass

    conn.commit()
    print(f"Weekly player stats seeded: {len(weekly)} rows processed")


def main():
    print(f"Connecting to {DATABASE_URL[:40]}...")
    conn = get_conn()
    try:
        print("\n1/3 Seeding teams...")
        seed_teams(conn)

        print("\n2/3 Seeding schedules...")
        seed_schedules(conn)

        print("\n3/3 Seeding player stats...")
        seed_weekly_player_stats(conn)

        print("\n✓ Seed complete!")
        print("Next: Run 'python analytics/updater.py' to train the ML models.")
    except Exception as e:
        conn.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
