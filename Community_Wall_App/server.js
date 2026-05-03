require('dotenv').config();
const express = require('express');
const session = require('express-session');
const bcrypt  = require('bcryptjs');
const path    = require('path');
const db      = require('./db');

const app  = express();
const PORT = process.env.PORT || 3000;

/* ── Middleware ── */
app.use(express.json());
app.use(express.static(__dirname));          // serves index.html + assets
app.use(session({
  secret:            process.env.SESSION_SECRET || 'busyhead-dev-change-in-prod',
  resave:            false,
  saveUninitialized: false,
  cookie: {
    maxAge:   7 * 24 * 60 * 60 * 1000,      // 7 days
    secure:   process.env.NODE_ENV === 'production',
    sameSite: 'lax',
  },
}));

const requireAuth = (req, res, next) => {
  if (!req.session.userId) return res.status(401).json({ error: 'Unauthorized' });
  next();
};

/* ═══════════════════════════════════════════ AUTH ═══ */

app.get('/api/status', (req, res) => {
  res.json({ ok: true, serverMode: true, loggedIn: !!req.session.userId });
});

app.get('/api/auth/me', (req, res) => {
  if (!req.session.userId) return res.json({ user: null });
  const user = db.prepare(
    'SELECT id, name, email, phone, avatar, healing_points, login_streak, created_at FROM users WHERE id = ?'
  ).get(req.session.userId);
  res.json({ user: user || null });
});

app.post('/api/auth/register', (req, res) => {
  const { name, email, password, phone } = req.body;
  if (!name || !email || !password || !phone)
    return res.status(400).json({ error: 'All fields are required.' });
  if (password.length < 6)
    return res.status(400).json({ error: 'Password must be at least 6 characters.' });

  const existing = db.prepare('SELECT id FROM users WHERE email = ?').get(email.toLowerCase());
  if (existing) return res.status(409).json({ error: 'An account with that email already exists. Sign in instead.' });

  const hash   = bcrypt.hashSync(password, 10);
  const result = db.prepare(
    'INSERT INTO users (name, email, password, phone) VALUES (?, ?, ?, ?)'
  ).run(name.trim(), email.toLowerCase().trim(), hash, phone.trim());

  req.session.userId = result.lastInsertRowid;
  db.prepare("UPDATE users SET last_login_date = date('now'), login_streak = 1 WHERE id = ?").run(result.lastInsertRowid);

  const user = db.prepare(
    'SELECT id, name, email, phone, avatar, healing_points, login_streak, created_at FROM users WHERE id = ?'
  ).get(result.lastInsertRowid);
  res.json({ user });
});

app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body;
  const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email?.toLowerCase().trim());
  if (!user)                         return res.status(401).json({ error: 'No account found with that email.' });
  if (!bcrypt.compareSync(password, user.password))
                                     return res.status(401).json({ error: 'Incorrect password.' });

  req.session.userId = user.id;

  // Handle daily login streak
  const today    = new Date().toISOString().split('T')[0];
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
  if (user.last_login_date !== today) {
    const newStreak = user.last_login_date === yesterday ? user.login_streak + 1 : 1;
    db.prepare('UPDATE users SET last_login_date = ?, login_streak = ?, healing_points = healing_points + 10 WHERE id = ?')
      .run(today, newStreak, user.id);
    db.prepare("INSERT INTO hp_log (user_id, amount, reason) VALUES (?, 10, 'Daily login bonus')").run(user.id);
  }

  const { password: _, ...safeUser } = db.prepare(
    'SELECT id, name, email, phone, avatar, healing_points, login_streak, created_at FROM users WHERE id = ?'
  ).get(user.id);
  res.json({ user: safeUser });
});

app.post('/api/auth/logout', (req, res) => {
  req.session.destroy(() => res.json({ ok: true }));
});

/* ═══════════════════════════════════════════ CARDS ══ */

app.get('/api/cards', (req, res) => {
  const rows = db.prepare(`
    SELECT c.id, c.user_id, c.prompt_idx, c.content, c.display_name, c.created_at
    FROM cards c
    ORDER BY c.created_at DESC
    LIMIT 300
  `).all();

  const cards = rows.map(c => {
    const rxnRows = db.prepare(
      'SELECT reaction_type, COUNT(*) as cnt FROM reactions WHERE card_id = ? GROUP BY reaction_type'
    ).all(c.id);
    const reactions = { leaf: 0, heart: 0, lightbulb: 0, mountain: 0 };
    rxnRows.forEach(r => { reactions[r.reaction_type] = r.cnt; });

    let userReactions = [];
    if (req.session.userId) {
      userReactions = db.prepare(
        'SELECT reaction_type FROM reactions WHERE card_id = ? AND user_id = ?'
      ).all(c.id, req.session.userId).map(r => r.reaction_type);
    }

    return { ...c, reactions, userReactions, isMine: c.user_id === req.session.userId };
  });

  res.json({ cards });
});

app.post('/api/cards', requireAuth, (req, res) => {
  const { promptIdx, content, displayName } = req.body;
  if (promptIdx === undefined || !content?.trim())
    return res.status(400).json({ error: 'Missing fields.' });
  if (content.length > 500)
    return res.status(400).json({ error: 'Response too long (max 500 characters).' });

  const id = 'c' + Date.now() + Math.random().toString(36).slice(2, 6);
  db.prepare(
    'INSERT INTO cards (id, user_id, prompt_idx, content, display_name) VALUES (?, ?, ?, ?, ?)'
  ).run(id, req.session.userId, promptIdx, content.trim(), displayName?.trim() || 'a voice from the community');

  // Award 5 Busyhead Bucks
  db.prepare('UPDATE users SET healing_points = healing_points + 5 WHERE id = ?').run(req.session.userId);
  db.prepare("INSERT INTO hp_log (user_id, amount, reason) VALUES (?, 5, 'Submitted a wall card')").run(req.session.userId);

  const card = db.prepare('SELECT * FROM cards WHERE id = ?').get(id);
  res.json({ card: { ...card, reactions: { leaf:0, heart:0, lightbulb:0, mountain:0 }, userReactions: [], isMine: true } });
});

app.delete('/api/cards/:id', requireAuth, (req, res) => {
  const card = db.prepare('SELECT * FROM cards WHERE id = ? AND user_id = ?').get(req.params.id, req.session.userId);
  if (!card) return res.status(403).json({ error: 'Card not found or not yours.' });
  db.prepare('DELETE FROM reactions WHERE card_id = ?').run(req.params.id);
  db.prepare('DELETE FROM cards WHERE id = ?').run(req.params.id);
  res.json({ ok: true });
});

/* ═══════════════════════════════════════════ REACTIONS */

app.post('/api/reactions', requireAuth, (req, res) => {
  const { cardId, type } = req.body;
  if (!cardId || !['leaf','heart','lightbulb','mountain'].includes(type))
    return res.status(400).json({ error: 'Invalid reaction.' });

  const existing = db.prepare(
    'SELECT id FROM reactions WHERE card_id = ? AND user_id = ? AND reaction_type = ?'
  ).get(cardId, req.session.userId, type);

  if (existing) {
    db.prepare('DELETE FROM reactions WHERE id = ?').run(existing.id);
    return res.json({ toggled: 'removed' });
  }
  db.prepare('INSERT INTO reactions (card_id, user_id, reaction_type) VALUES (?, ?, ?)').run(cardId, req.session.userId, type);
  res.json({ toggled: 'added' });
});

/* ═══════════════════════════════════════════ PROFILE ═ */

app.get('/api/profile', requireAuth, (req, res) => {
  const user = db.prepare(
    'SELECT id, name, email, avatar, healing_points, login_streak FROM users WHERE id = ?'
  ).get(req.session.userId);
  const myCards = db.prepare('SELECT * FROM cards WHERE user_id = ? ORDER BY created_at DESC').all(req.session.userId);
  const hpLog   = db.prepare('SELECT * FROM hp_log WHERE user_id = ? ORDER BY created_at DESC LIMIT 30').all(req.session.userId);
  res.json({ user, cards: myCards, hpLog });
});

app.patch('/api/profile', requireAuth, (req, res) => {
  const { name, avatar } = req.body;
  if (name) db.prepare('UPDATE users SET name = ? WHERE id = ?').run(name.trim(), req.session.userId);
  if (avatar) db.prepare('UPDATE users SET avatar = ? WHERE id = ?').run(avatar, req.session.userId);
  const user = db.prepare(
    'SELECT id, name, email, avatar, healing_points FROM users WHERE id = ?'
  ).get(req.session.userId);
  res.json({ user });
});

/* ═══════════════════════════════════════════ HP ═══════ */

app.post('/api/hp', requireAuth, (req, res) => {
  const { amount, reason } = req.body;
  if (typeof amount !== 'number') return res.status(400).json({ error: 'Invalid amount.' });
  db.prepare('UPDATE users SET healing_points = healing_points + ? WHERE id = ?').run(amount, req.session.userId);
  db.prepare('INSERT INTO hp_log (user_id, amount, reason) VALUES (?, ?, ?)').run(req.session.userId, amount, reason || '');
  const { healing_points } = db.prepare('SELECT healing_points FROM users WHERE id = ?').get(req.session.userId);
  res.json({ healing_points });
});

/* ═══════════════════════════════════════════ COMMUNITY */

app.get('/api/community/stats', (req, res) => {
  const totalCards   = db.prepare('SELECT COUNT(*) as n FROM cards').get().n;
  const totalUsers   = db.prepare('SELECT COUNT(*) as n FROM users').get().n;
  const totalReacts  = db.prepare('SELECT COUNT(*) as n FROM reactions').get().n;
  res.json({ totalCards, totalUsers, totalReacts });
});

/* ═══════════════════════════════════════════ SPA fallback */

app.use((_req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

/* ═══════════════════════════════════════════ START ══════ */

app.listen(PORT, () => {
  console.log(`\n🌲 The Busyhead Wall`);
  console.log(`🌿 Running at http://localhost:${PORT}\n`);
});
