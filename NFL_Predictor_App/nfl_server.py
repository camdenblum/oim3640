// ============================================================
//  NFL PREDICTOR PROXY SERVER
//  Run: node server.js
//  Requires: .env file with your API keys (see README below)
// ============================================================

import express from 'express'
import fetch from 'node-fetch'
import cors from 'cors'
import cron from 'node-cron'
import { WebSocketServer } from 'ws'
import { createServer } from 'http'
import { readFileSync, existsSync } from 'fs'
import { config } from 'dotenv'

config() // load .env

const app = express()
const server = createServer(app)
const wss = new WebSocketServer({ server })

// ── CONFIG ────────────────────────────────────────────────────────────────────
const PORT          = process.env.PORT || 3001
const ODDS_KEY      = process.env.ODDS_API_KEY || ''
const ANTHROPIC_KEY = process.env.ANTHROPIC_KEY || ''
const CACHE_TTL     = 5 * 60 * 1000   // 5 minutes default
const SCORES_TTL    = 30 * 1000        // 30 seconds for live scores

// ── CORS: allow browser file:// and localhost ─────────────────────────────────
app.use(cors({
  origin: (origin, cb) => cb(null, true), // allow all origins (local use only)
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization']
}))
app.use(express.json())

// ── IN-MEMORY CACHE ───────────────────────────────────────────────────────────
const cache = new Map()

function getCache(key) {
  const entry = cache.get(key)
  if (!entry) return null
  if (Date.now() - entry.ts > entry.ttl) { cache.delete(key); return null }
  return entry.data
}

function setCache(key, data, ttl = CACHE_TTL) {
  cache.set(key, { data, ts: Date.now(), ttl })
}

// ── LOGGING ───────────────────────────────────────────────────────────────────
function log(emoji, msg) {
  console.log(`${new Date().toLocaleTimeString()} ${emoji}  ${msg}`)
}

// ══════════════════════════════════════════════════════════════════════════════
//  ROUTES
// ══════════════════════════════════════════════════════════════════════════════

// ── Health check ──────────────────────────────────────────────────────────────
app.get('/', (req, res) => {
  res.json({
    status: 'running',
    version: '1.0.0',
    endpoints: [
      'GET  /odds              - Live NFL moneylines, spreads, totals',
      'GET  /odds/props        - Live player props (requires Odds API)',
      'GET  /schedule          - NFL schedule (?week=1&season=2026)',
      'GET  /scores            - Live in-progress scores',
      'GET  /scores/live       - Alias for /scores',
      'GET  /teams             - All 32 NFL teams',
      'GET  /teams/:id/stats   - Team season statistics',
      'GET  /teams/:id/roster  - Team roster',
      'GET  /players/:id/stats - Player game log',
      'GET  /standings         - Current NFL standings',
      'GET  /injuries          - League-wide injury report',
      'GET  /news              - NFL headlines',
      'POST /predict           - AI prediction (proxies Anthropic API)',
      'GET  /cache/status      - Cache stats',
      'GET  /cache/clear       - Clear all caches',
    ],
    odds_api_connected: !!ODDS_KEY,
    anthropic_connected: !!ANTHROPIC_KEY,
  })
})

// ── LIVE ODDS (The Odds API) ──────────────────────────────────────────────────
app.get('/odds', async (req, res) => {
  const cacheKey = 'odds_h2h_spreads'
  const cached = getCache(cacheKey)
  if (cached) {
    log('💾', 'Serving odds from cache')
    return res.json({ source: 'cache', data: cached })
  }

  if (!ODDS_KEY) {
    log('⚠️', 'No ODDS_API_KEY — returning demo odds')
    return res.json({ source: 'demo', data: getDemoOdds() })
  }

  try {
    log('📡', 'Fetching live odds from The Odds API...')
    const url = [
      'https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds/',
      `?apiKey=${ODDS_KEY}`,
      '&regions=us',
      '&markets=h2h,spreads,totals',
      '&oddsFormat=american',
      '&bookmakers=draftkings,fanduel,betmgm,caesars,pointsbet'
    ].join('')

    const r = await fetch(url)
    const remaining  = r.headers.get('x-requests-remaining')
    const used       = r.headers.get('x-requests-used')

    if (!r.ok) {
      const err = await r.json()
      throw new Error(err.message || `HTTP ${r.status}`)
    }

    const data = await r.json()
    setCache(cacheKey, data, CACHE_TTL)

    log('✅', `Odds fetched — ${data.length} games | requests remaining: ${remaining}`)
    res.json({
      source: 'live',
      data,
      meta: { remaining, used, cached_until: new Date(Date.now() + CACHE_TTL).toISOString() }
    })
  } catch (e) {
    log('❌', `Odds error: ${e.message}`)
    res.status(500).json({ error: e.message, data: getDemoOdds(), source: 'fallback' })
  }
})

// ── PLAYER PROPS ODDS ─────────────────────────────────────────────────────────
app.get('/odds/props', async (req, res) => {
  const { player_prop = 'player_pass_yds,player_rush_yds,player_reception_yds' } = req.query
  const cacheKey = `odds_props_${player_prop}`
  const cached = getCache(cacheKey)
  if (cached) return res.json({ source: 'cache', data: cached })

  if (!ODDS_KEY) return res.json({ source: 'demo', data: [] })

  try {
    log('📡', 'Fetching player props...')
    const url = [
      'https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds/',
      `?apiKey=${ODDS_KEY}`,
      '&regions=us',
      `&markets=${player_prop}`,
      '&oddsFormat=american',
      '&bookmakers=draftkings,fanduel'
    ].join('')

    const r = await fetch(url)
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const data = await r.json()
    setCache(cacheKey, data, CACHE_TTL)
    res.json({ source: 'live', data })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

// ── NFL SCHEDULE (ESPN — no key required) ─────────────────────────────────────
app.get('/schedule', async (req, res) => {
  const { week = 1, season = 2026, type = 2 } = req.query
  // type: 1=preseason, 2=regular, 3=postseason
  const cacheKey = `schedule_${season}_${week}_${type}`
  const cached = getCache(cacheKey)
  if (cached) return res.json({ source: 'cache', data: cached })

  try {
    log('📅', `Fetching schedule: season=${season} week=${week}`)
    const url = `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=${type}&week=${week}&dates=${season}`
    const r = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
    if (!r.ok) throw new Error(`ESPN returned ${r.status}`)
    const raw = await r.json()

    // Normalize into a cleaner shape
    const games = (raw.events || []).map(ev => {
      const comp  = ev.competitions?.[0] || {}
      const home  = comp.competitors?.find(c => c.homeAway === 'home') || {}
      const away  = comp.competitors?.find(c => c.homeAway === 'away') || {}
      return {
        id:           ev.id,
        name:         ev.name,
        date:         ev.date,
        week:         week,
        season:       season,
        status:       comp.status?.type?.description || 'Scheduled',
        status_state: comp.status?.type?.state || 'pre',
        clock:        comp.status?.displayClock || '',
        period:       comp.status?.period || 0,
        venue:        comp.venue?.fullName || '',
        venue_city:   comp.venue?.address?.city || '',
        neutral_site: comp.neutralSite || false,
        home: {
          id:     home.id,
          abbr:   home.team?.abbreviation,
          name:   home.team?.displayName,
          score:  home.score || '0',
          record: home.records?.[0]?.summary || '',
          logo:   home.team?.logo,
        },
        away: {
          id:     away.id,
          abbr:   away.team?.abbreviation,
          name:   away.team?.displayName,
          score:  away.score || '0',
          record: away.records?.[0]?.summary || '',
          logo:   away.team?.logo,
        },
        odds: comp.odds?.[0] || null,
        broadcast: comp.broadcasts?.[0]?.names?.[0] || '',
      }
    })

    const normalized = { week, season, game_count: games.length, games }
    setCache(cacheKey, normalized, CACHE_TTL)
    res.json({ source: 'live', data: normalized })
  } catch (e) {
    log('❌', `Schedule error: ${e.message}`)
    res.status(500).json({ error: e.message })
  }
})

// ── LIVE SCORES ───────────────────────────────────────────────────────────────
app.get(['/scores', '/scores/live'], async (req, res) => {
  const cacheKey = 'scores_live'
  const cached = getCache(cacheKey)
  if (cached) return res.json({ source: 'cache', data: cached })

  try {
    log('🏈', 'Fetching live scores...')
    const url = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard'
    const r = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
    const raw = await r.json()

    const scores = (raw.events || []).map(ev => {
      const comp = ev.competitions?.[0] || {}
      const home = comp.competitors?.find(c => c.homeAway === 'home') || {}
      const away = comp.competitors?.find(c => c.homeAway === 'away') || {}
      return {
        id:           ev.id,
        name:         ev.shortName || ev.name,
        status:       comp.status?.type?.description,
        state:        comp.status?.type?.state,
        clock:        comp.status?.displayClock,
        quarter:      comp.status?.period,
        home_team:    home.team?.abbreviation,
        home_score:   home.score,
        away_team:    away.team?.abbreviation,
        away_score:   away.score,
        possession:   comp.situation?.possession || null,
        down_distance:comp.situation?.downDistanceText || null,
        last_play:    comp.situation?.lastPlay?.text || null,
        red_zone:     comp.situation?.isRedZone || false,
      }
    })

    const data = {
      timestamp: new Date().toISOString(),
      live_games: scores.filter(s => s.state === 'in'),
      upcoming:   scores.filter(s => s.state === 'pre'),
      final:      scores.filter(s => s.state === 'post'),
    }

    setCache(cacheKey, data, SCORES_TTL)
    res.json({ source: 'live', data })
  } catch (e) {
    log('❌', `Scores error: ${e.message}`)
    res.status(500).json({ error: e.message })
  }
})

// ── ALL 32 TEAMS ──────────────────────────────────────────────────────────────
app.get('/teams', async (req, res) => {
  const cached = getCache('all_teams')
  if (cached) return res.json({ source: 'cache', data: cached })

  try {
    const url = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams?limit=32'
    const r   = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
    const raw = await r.json()

    const teams = (raw.sports?.[0]?.leagues?.[0]?.teams || []).map(t => ({
      id:           t.team.id,
      abbr:         t.team.abbreviation,
      name:         t.team.displayName,
      short_name:   t.team.shortDisplayName,
      nickname:     t.team.name,
      city:         t.team.location,
      color:        t.team.color,
      logo:         t.team.logos?.[0]?.href,
      conference:   t.team.groups?.parent?.name || '',
      division:     t.team.groups?.name || '',
    }))

    setCache('all_teams', teams, 24 * 60 * 60 * 1000) // 24hr cache
    res.json({ source: 'live', data: teams })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

// ── TEAM STATS ────────────────────────────────────────────────────────────────
app.get('/teams/:id/stats', async (req, res) => {
  const { id } = req.params
  const { season = 2026 } = req.query
  const cacheKey = `team_stats_${id}_${season}`
  const cached   = getCache(cacheKey)
  if (cached) return res.json({ source: 'cache', data: cached })

  try {
    log('📊', `Fetching stats for team ${id}`)
    const url = `https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/${id}/statistics?season=${season}`
    const r   = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
    if (!r.ok) throw new Error(`ESPN returned ${r.status}`)
    const data = await r.json()

    // Flatten stat categories
    const flat = {}
    ;(data.results?.stats?.categories || []).forEach(cat => {
      ;(cat.stats || []).forEach(s => {
        flat[`${cat.name}_${s.name}`] = { value: s.value, rank: s.rank, display: s.displayValue }
      })
    })

    const result = { team_id: id, season, raw: data, flat }
    setCache(cacheKey, result, 60 * 60 * 1000) // 1hr
    res.json({ source: 'live', data: result })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

// ── TEAM ROSTER ───────────────────────────────────────────────────────────────
app.get('/teams/:id/roster', async (req, res) => {
  const { id } = req.params
  const cacheKey = `roster_${id}`
  const cached   = getCache(cacheKey)
  if (cached) return res.json({ source: 'cache', data: cached })

  try {
    const url = `https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/${id}/roster`
    const r   = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
    if (!r.ok) throw new Error(`ESPN returned ${r.status}`)
    const data = await r.json()

    const players = (data.athletes || []).flatMap(group =>
      (group.items || []).map(p => ({
        id:       p.id,
        name:     p.displayName,
        position: p.position?.abbreviation,
        jersey:   p.jersey,
        status:   p.status?.type,
        injury:   p.injuries?.[0]?.type?.description || null,
      }))
    )

    setCache(cacheKey, players, 60 * 60 * 1000)
    res.json({ source: 'live', data: players })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

// ── PLAYER STATS ──────────────────────────────────────────────────────────────
app.get('/players/:id/stats', async (req, res) => {
  const { id } = req.params
  const { season = 2026 } = req.query
  const cacheKey = `player_stats_${id}_${season}`
  const cached   = getCache(cacheKey)
  if (cached) return res.json({ source: 'cache', data: cached })

  try {
    const url = `https://site.api.espn.com/apis/site/v2/sports/football/nfl/athletes/${id}/splits?season=${season}`
    const r   = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
    if (!r.ok) throw new Error(`ESPN returned ${r.status}`)
    const data = await r.json()
    setCache(cacheKey, data, 60 * 60 * 1000)
    res.json({ source: 'live', data })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

// ── STANDINGS ─────────────────────────────────────────────────────────────────
app.get('/standings', async (req, res) => {
  const { season = 2026 } = req.query
  const cacheKey = `standings_${season}`
  const cached   = getCache(cacheKey)
  if (cached) return res.json({ source: 'cache', data: cached })

  try {
    log('🏆', 'Fetching standings...')
    const url = `https://site.api.espn.com/apis/v2/sports/football/nfl/standings?season=${season}`
    const r   = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
    if (!r.ok) throw new Error(`ESPN returned ${r.status}`)
    const data = await r.json()

    const divisions = (data.children || []).flatMap(conf =>
      (conf.children || []).map(div => ({
        conference: conf.name,
        division:   div.name,
        teams: (div.standings?.entries || []).map(e => ({
          id:     e.team?.id,
          abbr:   e.team?.abbreviation,
          name:   e.team?.displayName,
          wins:   e.stats?.find(s => s.name === 'wins')?.value,
          losses: e.stats?.find(s => s.name === 'losses')?.value,
          ties:   e.stats?.find(s => s.name === 'ties')?.value,
          pct:    e.stats?.find(s => s.name === 'winPercent')?.value,
          pf:     e.stats?.find(s => s.name === 'pointsFor')?.value,
          pa:     e.stats?.find(s => s.name === 'pointsAgainst')?.value,
          streak: e.stats?.find(s => s.name === 'streak')?.displayValue,
          clinched: e.stats?.find(s => s.name === 'playoffSeed')?.value,
        }))
      }))
    )

    setCache(cacheKey, divisions, 60 * 60 * 1000)
    res.json({ source: 'live', data: divisions })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

// ── INJURIES ──────────────────────────────────────────────────────────────────
app.get('/injuries', async (req, res) => {
  const cacheKey = 'injuries'
  const cached   = getCache(cacheKey)
  if (cached) return res.json({ source: 'cache', data: cached })

  try {
    log('🏥', 'Fetching injury reports...')
    // ESPN injuries endpoint
    const url = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries'
    const r   = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
    if (!r.ok) throw new Error(`ESPN returned ${r.status}`)
    const data = await r.json()

    const injuries = (data.injuries || []).map(item => ({
      team:     item.team?.displayName,
      team_abbr:item.team?.abbreviation,
      player:   item.athlete?.displayName,
      position: item.athlete?.position?.abbreviation,
      status:   item.status,
      injury:   item.details?.type,
      side:     item.details?.location,
      return_date: item.details?.returnDate || 'TBD',
    }))

    setCache(cacheKey, injuries, 30 * 60 * 1000) // 30min
    res.json({ source: 'live', data: injuries })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

// ── NFL NEWS ──────────────────────────────────────────────────────────────────
app.get('/news', async (req, res) => {
  const { limit = 20 } = req.query
  const cacheKey = `news_${limit}`
  const cached   = getCache(cacheKey)
  if (cached) return res.json({ source: 'cache', data: cached })

  try {
    const url = `https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=${limit}`
    const r   = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
    if (!r.ok) throw new Error(`ESPN returned ${r.status}`)
    const data = await r.json()

    const articles = (data.articles || []).map(a => ({
      id:          a.id,
      headline:    a.headline,
      description: a.description,
      published:   a.published,
      url:         a.links?.web?.href,
      image:       a.images?.[0]?.url,
      categories:  a.categories?.map(c => c.description).filter(Boolean),
    }))

    setCache(cacheKey, articles, 15 * 60 * 1000)
    res.json({ source: 'live', data: articles })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

// ── ANTHROPIC PREDICT PROXY ───────────────────────────────────────────────────
// This keeps your API key server-side — never exposed to the browser
app.post('/predict', async (req, res) => {
  const key = ANTHROPIC_KEY
  if (!key) return res.status(400).json({ error: 'No ANTHROPIC_KEY set in .env' })

  const { prompt, max_tokens = 1000 } = req.body
  if (!prompt) return res.status(400).json({ error: 'prompt is required' })

  try {
    log('🤖', 'Proxying Anthropic request...')
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type':    'application/json',
        'x-api-key':       key,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model:      'claude-sonnet-4-20250514',
        max_tokens,
        messages:   [{ role: 'user', content: prompt }]
      })
    })

    if (!r.ok) {
      const err = await r.json()
      throw new Error(err.error?.message || `Anthropic HTTP ${r.status}`)
    }

    const data = await r.json()
    res.json({ text: data.content[0].text })
  } catch (e) {
    log('❌', `Anthropic error: ${e.message}`)
    res.status(500).json({ error: e.message })
  }
})

// ── CACHE MANAGEMENT ──────────────────────────────────────────────────────────
app.get('/cache/status', (req, res) => {
  const entries = []
  cache.forEach((v, k) => {
    const age = Math.round((Date.now() - v.ts) / 1000)
    const ttlLeft = Math.round((v.ttl - (Date.now() - v.ts)) / 1000)
    entries.push({ key: k, age_seconds: age, ttl_remaining_seconds: Math.max(0, ttlLeft) })
  })
  res.json({ cache_size: cache.size, entries })
})

app.get('/cache/clear', (req, res) => {
  const size = cache.size
  cache.clear()
  log('🗑️', `Cache cleared (${size} entries removed)`)
  res.json({ cleared: size })
})

// ══════════════════════════════════════════════════════════════════════════════
//  WEBSOCKET — push live scores to connected clients
// ══════════════════════════════════════════════════════════════════════════════

wss.on('connection', (ws) => {
  log('🔌', 'WebSocket client connected')

  ws.send(JSON.stringify({ type: 'connected', message: 'NFL Proxy WebSocket ready' }))

  ws.on('close', () => log('🔌', 'WebSocket client disconnected'))
  ws.on('error', (e) => log('❌', `WebSocket error: ${e.message}`))
})

function broadcast(data) {
  const msg = JSON.stringify(data)
  wss.clients.forEach(client => {
    if (client.readyState === 1) client.send(msg)
  })
}

// Push live scores every 30 seconds
setInterval(async () => {
  if (wss.clients.size === 0) return
  try {
    const url = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard'
    const r   = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
    const raw = await r.json()

    const live = (raw.events || []).filter(ev =>
      ev.competitions?.[0]?.status?.type?.state === 'in'
    )

    if (live.length > 0) {
      log('📡', `Broadcasting ${live.length} live game(s) to ${wss.clients.size} client(s)`)
      broadcast({ type: 'live_scores', timestamp: new Date().toISOString(), games: live })
    }
  } catch (e) {
    // silently ignore broadcast errors
  }
}, 30000)

// ══════════════════════════════════════════════════════════════════════════════
//  CRON JOBS — auto-refresh cache during game hours
// ══════════════════════════════════════════════════════════════════════════════

// Every 4 minutes on Sunday (game day) 11am-midnight ET
cron.schedule('*/4 11-23 * * 0', () => {
  log('⏰', 'Sunday cron: invalidating odds + scores cache')
  cache.delete('odds_h2h_spreads')
  cache.delete('scores_live')
})

// Every 5 minutes on Monday 7pm-midnight (MNF)
cron.schedule('*/5 19-23 * * 1', () => {
  cache.delete('odds_h2h_spreads')
  cache.delete('scores_live')
})

// Every 5 minutes on Thursday 7pm-midnight (TNF)
cron.schedule('*/5 19-23 * * 4', () => {
  cache.delete('odds_h2h_spreads')
  cache.delete('scores_live')
})

// Daily standings + injuries refresh at 6am
cron.schedule('0 6 * * *', () => {
  log('🌅', 'Daily refresh: clearing standings + injuries cache')
  ;[...cache.keys()]
    .filter(k => k.startsWith('standings') || k === 'injuries')
    .forEach(k => cache.delete(k))
})

// ══════════════════════════════════════════════════════════════════════════════
//  DEMO DATA FALLBACK
// ══════════════════════════════════════════════════════════════════════════════

function getDemoOdds() {
  return [
    {
      id: 'kc_buf_2026', sport_key: 'americanfootball_nfl',
      home_team: 'Kansas City Chiefs', away_team: 'Buffalo Bills',
      commence_time: new Date(Date.now() + 3 * 24 * 3600 * 1000).toISOString(),
      bookmakers: [
        { title: 'DraftKings', markets: [
          { key: 'h2h', outcomes: [{ name: 'Kansas City Chiefs', price: -145 }, { name: 'Buffalo Bills', price: 122 }] },
          { key: 'spreads', outcomes: [{ name: 'Kansas City Chiefs', price: -110, point: -3 }, { name: 'Buffalo Bills', price: -110, point: 3 }] },
          { key: 'totals', outcomes: [{ name: 'Over', price: -110, point: 49.5 }, { name: 'Under', price: -110, point: 49.5 }] },
        ]},
        { title: 'FanDuel', markets: [
          { key: 'h2h', outcomes: [{ name: 'Kansas City Chiefs', price: -148 }, { name: 'Buffalo Bills', price: 125 }] },
          { key: 'spreads', outcomes: [{ name: 'Kansas City Chiefs', price: -112, point: -3 }, { name: 'Buffalo Bills', price: -108, point: 3 }] },
        ]},
        { title: 'BetMGM', markets: [
          { key: 'h2h', outcomes: [{ name: 'Kansas City Chiefs', price: -142 }, { name: 'Buffalo Bills', price: 118 }] },
          { key: 'spreads', outcomes: [{ name: 'Kansas City Chiefs', price: -110, point: -3.5 }, { name: 'Buffalo Bills', price: -110, point: 3.5 }] },
        ]},
      ]
    },
    {
      id: 'phi_dal_2026', sport_key: 'americanfootball_nfl',
      home_team: 'Philadelphia Eagles', away_team: 'Dallas Cowboys',
      commence_time: new Date(Date.now() + 3 * 24 * 3600 * 1000).toISOString(),
      bookmakers: [
        { title: 'DraftKings', markets: [
          { key: 'h2h', outcomes: [{ name: 'Philadelphia Eagles', price: -240 }, { name: 'Dallas Cowboys', price: 198 }] },
          { key: 'spreads', outcomes: [{ name: 'Philadelphia Eagles', price: -110, point: -5.5 }, { name: 'Dallas Cowboys', price: -110, point: 5.5 }] },
          { key: 'totals', outcomes: [{ name: 'Over', price: -110, point: 44 }, { name: 'Under', price: -110, point: 44 }] },
        ]},
        { title: 'FanDuel', markets: [
          { key: 'h2h', outcomes: [{ name: 'Philadelphia Eagles', price: -235 }, { name: 'Dallas Cowboys', price: 195 }] },
        ]},
      ]
    },
    {
      id: 'bal_cin_2026', sport_key: 'americanfootball_nfl',
      home_team: 'Baltimore Ravens', away_team: 'Cincinnati Bengals',
      commence_time: new Date(Date.now() + 3 * 24 * 3600 * 1000).toISOString(),
      bookmakers: [
        { title: 'DraftKings', markets: [
          { key: 'h2h', outcomes: [{ name: 'Baltimore Ravens', price: -175 }, { name: 'Cincinnati Bengals', price: 148 }] },
          { key: 'spreads', outcomes: [{ name: 'Baltimore Ravens', price: -110, point: -3.5 }, { name: 'Cincinnati Bengals', price: -110, point: 3.5 }] },
          { key: 'totals', outcomes: [{ name: 'Over', price: -112, point: 46.5 }, { name: 'Under', price: -108, point: 46.5 }] },
        ]},
      ]
    },
    {
      id: 'sf_lar_2026', sport_key: 'americanfootball_nfl',
      home_team: 'San Francisco 49ers', away_team: 'Los Angeles Rams',
      commence_time: new Date(Date.now() + 3 * 24 * 3600 * 1000).toISOString(),
      bookmakers: [
        { title: 'DraftKings', markets: [
          { key: 'h2h', outcomes: [{ name: 'San Francisco 49ers', price: -205 }, { name: 'Los Angeles Rams', price: 170 }] },
          { key: 'spreads', outcomes: [{ name: 'San Francisco 49ers', price: -108, point: -4.5 }, { name: 'Los Angeles Rams', price: -112, point: 4.5 }] },
          { key: 'totals', outcomes: [{ name: 'Over', price: -110, point: 45 }, { name: 'Under', price: -110, point: 45 }] },
        ]},
      ]
    },
  ]
}

// ══════════════════════════════════════════════════════════════════════════════
//  START
// ══════════════════════════════════════════════════════════════════════════════

server.listen(PORT, () => {
  console.log('\n')
  console.log('  ╔══════════════════════════════════════════╗')
  console.log('  ║   🏈  NFL PREDICTOR PROXY  v1.0          ║')
  console.log('  ╚══════════════════════════════════════════╝')
  console.log(`\n  Local:   http://localhost:${PORT}`)
  console.log(`  WS:      ws://localhost:${PORT}`)
  console.log(`\n  Odds API:     ${ODDS_KEY ? '✅ connected' : '⚠️  no key (demo mode)'}`)
  console.log(`  Anthropic:    ${ANTHROPIC_KEY ? '✅ connected' : '⚠️  no key set'}`)
  console.log('\n  Endpoints:')
  console.log('  GET  /odds           - Live odds')
  console.log('  GET  /schedule       - NFL schedule')
  console.log('  GET  /scores         - Live scores')
  console.log('  GET  /standings      - Standings')
  console.log('  GET  /injuries       - Injury report')
  console.log('  GET  /news           - NFL news')
  console.log('  POST /predict        - AI predictions')
  console.log('\n  Press Ctrl+C to stop\n')
})
