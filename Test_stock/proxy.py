/**
 * ============================================================
 *  STOCK PREDICTOR — LOCAL PROXY SERVER
 *  Run this in VSCode terminal, then open stock-predictor.html
 * ============================================================
 *
 *  SETUP (one time):
 *    1. Install Node.js from https://nodejs.org (LTS version)
 *    2. Open this folder in VSCode
 *    3. Open the terminal (Ctrl+` or View > Terminal)
 *    4. Run:  npm install
 *    5. Paste your Anthropic API key below (line ~30)
 *    6. Run:  node proxy-server.js
 *    7. Open stock-predictor.html in your browser
 *
 *  REQUIREMENTS:
 *    npm install express cors node-fetch
 *
 *  Your API key never leaves your machine.
 * ============================================================
 */

const express  = require('express');
const cors     = require('cors');
const path     = require('path');

// ─────────────────────────────────────────────
//  PASTE YOUR ANTHROPIC API KEY HERE
//  Get one free at https://console.anthropic.com
// ─────────────────────────────────────────────
const ANTHROPIC_API_KEY = 'YOUR_ANTHROPIC_API_KEY_HERE';
// ─────────────────────────────────────────────

const PORT = 3000;
const app  = express();

app.use(cors());
app.use(express.json());

// Serve the HTML file directly
app.use(express.static(path.dirname(__filename)));

// ── Health check ──────────────────────────────
app.get('/health', (req, res) => {
  const keySet = ANTHROPIC_API_KEY !== 'YOUR_ANTHROPIC_API_KEY_HERE' && ANTHROPIC_API_KEY.length > 10;
  res.json({
    status : 'ok',
    keySet,
    message: keySet ? 'API key configured. Ready to analyze.' : 'WARNING: API key not set in proxy-server.js'
  });
});

// ── Main proxy endpoint ───────────────────────
app.post('/api/analyze', async (req, res) => {
  if (ANTHROPIC_API_KEY === 'YOUR_ANTHROPIC_API_KEY_HERE') {
    return res.status(500).json({
      error: 'API key not configured. Open proxy-server.js and paste your Anthropic API key on line ~30.'
    });
  }

  try {
    // Dynamically import node-fetch (works with both CommonJS and ESM)
    const fetch = (await import('node-fetch')).default;

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method : 'POST',
      headers: {
        'Content-Type'      : 'application/json',
        'x-api-key'         : ANTHROPIC_API_KEY,
        'anthropic-version' : '2023-06-01'
      },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();

    if (!response.ok) {
      console.error('Anthropic API error:', data);
      return res.status(response.status).json({ error: data?.error?.message || 'Anthropic API error' });
    }

    res.json(data);
  } catch (err) {
    console.error('Proxy error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── Start ─────────────────────────────────────
app.listen(PORT, () => {
  const keySet = ANTHROPIC_API_KEY !== 'YOUR_ANTHROPIC_API_KEY_HERE';
  console.log('');
  console.log('  ┌─────────────────────────────────────────┐');
  console.log('  │   Stock Predictor — Proxy Server         │');
  console.log('  ├─────────────────────────────────────────┤');
  console.log(`  │   Running at: http://localhost:${PORT}       │`);
  console.log(`  │   API Key:    ${keySet ? '✓ Configured             ' : '✗ NOT SET — edit proxy-server.js'} │`);
  console.log('  ├─────────────────────────────────────────┤');
  console.log('  │   Open stock-predictor.html in browser  │');
  console.log('  │   or visit http://localhost:3000        │');
  console.log('  └─────────────────────────────────────────┘');
  console.log('');
  if (!keySet) {
    console.log('  ⚠  ACTION REQUIRED: Open proxy-server.js');
    console.log('     and replace YOUR_ANTHROPIC_API_KEY_HERE');
    console.log('     with your real key from console.anthropic.com');
    console.log('');
  }
});
