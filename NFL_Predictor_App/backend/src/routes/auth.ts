import { Router } from 'express';
import { asyncHandler } from '../middleware/errorHandler';
import { pool } from '../database/connection';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';

const router = Router();

router.post('/register', asyncHandler(async (req, res) => {
  const { email, password, name } = req.body;
  if (!email || !password) { res.status(400).json({ success: false, data: null, error: 'Email and password required' }); return; }
  const hash = await bcrypt.hash(password, 12);
  const { rows } = await pool.query(
    'INSERT INTO users (email, password_hash, name, role) VALUES ($1, $2, $3, $4) RETURNING id, email, name, role',
    [email, hash, name || email, 'viewer']
  );
  const token = jwt.sign(rows[0], process.env.JWT_SECRET || 'secret', { expiresIn: '7d' });
  res.json({ success: true, data: { user: rows[0], token } });
}));

router.post('/login', asyncHandler(async (req, res) => {
  const { email, password } = req.body;
  const { rows } = await pool.query('SELECT * FROM users WHERE email = $1', [email]);
  if (!rows.length || !(await bcrypt.compare(password, rows[0].password_hash))) {
    res.status(401).json({ success: false, data: null, error: 'Invalid credentials' });
    return;
  }
  const { password_hash, ...user } = rows[0];
  const token = jwt.sign(user, process.env.JWT_SECRET || 'secret', { expiresIn: '7d' });
  res.json({ success: true, data: { user, token } });
}));

export default router;
