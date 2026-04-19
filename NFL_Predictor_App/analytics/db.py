import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://nfl_user:nfl_password@localhost:5432/nfl_predictor")

@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

def query(sql: str, params=None):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or [])
            return cur.fetchall()

def execute(sql: str, params=None):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or [])
        conn.commit()
