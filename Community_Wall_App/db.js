const Database = require('better-sqlite3');
const path     = require('path');
const fs       = require('fs');

const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

const db = new Database(path.join(dataDir, 'busyhead.db'));

db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    email           TEXT    UNIQUE NOT NULL,
    password        TEXT    NOT NULL,
    phone           TEXT,
    avatar          TEXT    DEFAULT 'mountain',
    healing_points  INTEGER DEFAULT 0,
    login_streak    INTEGER DEFAULT 0,
    last_login_date TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS cards (
    id           TEXT    PRIMARY KEY,
    user_id      INTEGER REFERENCES users(id) ON DELETE SET NULL,
    prompt_idx   INTEGER NOT NULL,
    content      TEXT    NOT NULL,
    display_name TEXT    DEFAULT 'a voice from the community',
    created_at   TEXT    DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS reactions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id       TEXT    REFERENCES cards(id)  ON DELETE CASCADE,
    user_id       INTEGER REFERENCES users(id)  ON DELETE CASCADE,
    reaction_type TEXT    NOT NULL CHECK(reaction_type IN ('leaf','heart','lightbulb','mountain')),
    created_at    TEXT    DEFAULT (datetime('now')),
    UNIQUE(card_id, user_id, reaction_type)
  );

  CREATE TABLE IF NOT EXISTS checkins (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER REFERENCES users(id) ON DELETE CASCADE,
    mood_score   INTEGER NOT NULL CHECK(mood_score BETWEEN 1 AND 5),
    checkin_date TEXT    DEFAULT (date('now')),
    UNIQUE(user_id, checkin_date)
  );

  CREATE TABLE IF NOT EXISTS hp_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount     INTEGER NOT NULL,
    reason     TEXT,
    created_at TEXT DEFAULT (datetime('now'))
  );

  -- Seed sample cards if table is empty
  INSERT OR IGNORE INTO cards (id, user_id, prompt_idx, content, display_name) VALUES
    ('s1', NULL, 0, 'That it isn''t about "just being sad." It''s a heaviness that makes even the smallest tasks feel impossible. And that doesn''t mean I''m not trying.', 'Mara'),
    ('s2', NULL, 4, 'Music. Specifically the moment a song puts words to something I''ve been feeling but couldn''t name. That feeling of being understood without having to explain.', 'a voice from the community'),
    ('s3', NULL, 2, 'That it''s okay if today was not the day you figured it out. You don''t have to have it together right now. You just have to be here. The rest can wait.', 'Jamie'),
    ('s4', NULL, 1, 'Honestly? Walks. Just getting outside and letting my feet carry me somewhere without any plan. The rhythm of it quiets things down.', 'a voice from the community'),
    ('s5', NULL, 3, 'For the years I spent convincing myself I was fine. I lost time I could have spent getting better, because I was too proud to admit I needed help.', 'Eli'),
    ('s6', NULL, 4, 'My dog. She doesn''t know what I''m carrying but she leans into me like she does. Some days that''s the only thing that''s gotten me out of bed.', 'a voice from the community'),
    ('s7', NULL, 2, 'That the person who reaches out is braver than you know. Sending one text, making one call — those things take more courage than most people realize.', 'Taylor'),
    ('s8', NULL, 0, 'That being high-functioning doesn''t mean you''re fine. I showed up to work every day. I laughed at things. Nobody knew. Invisible doesn''t mean it isn''t real.', 'a voice from the community');
`);

module.exports = db;
