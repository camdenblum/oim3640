import { Router } from 'express';
import axios from 'axios';
import { asyncHandler } from '../middleware/errorHandler';
import { AnalyticsService } from '../services/analyticsService';
import { cacheGet, cacheSet } from '../config/redis';

const router = Router();
const svc = new AnalyticsService();
const analyticsUrl = process.env.ANALYTICS_SERVICE_URL || 'http://localhost:8001';

router.get('/standings', asyncHandler(async (req, res) => {
  const cacheKey = `analytics:standings:${req.query.season || 'current'}`;
  const cached = await cacheGet(cacheKey);
  if (cached) { res.json({ success: true, data: cached }); return; }
  const data = await svc.getStandings(Number(req.query.season));
  await cacheSet(cacheKey, data, 3600);
  res.json({ success: true, data });
}));

router.get('/power-rankings', asyncHandler(async (req, res) => {
  const data = await svc.getPowerRankings(Number(req.query.week), Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/schedule-difficulty', asyncHandler(async (req, res) => {
  const data = await svc.getScheduleDifficulty(Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/trends', asyncHandler(async (req, res) => {
  const data = await svc.getLeagueTrends(Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/matchups/:gameId', asyncHandler(async (req, res) => {
  const data = await svc.getMatchupAnalysis(Number(req.params.gameId));
  res.json({ success: true, data });
}));

router.get('/weather', asyncHandler(async (req, res) => {
  const data = await svc.getWeatherImpact(Number(req.query.week));
  res.json({ success: true, data });
}));

router.get('/officials', asyncHandler(async (req, res) => {
  const data = await svc.getOfficialsData(Number(req.query.week), Number(req.query.season));
  res.json({ success: true, data });
}));

// Proxy feature importance from Python analytics service
router.get('/feature-importance', asyncHandler(async (req, res) => {
  try {
    const response = await axios.get(`${analyticsUrl}/model/feature-importance`, { timeout: 10000 });
    res.json({ success: true, data: response.data });
  } catch {
    res.json({ success: true, data: { importance: [], message: 'Analytics service not available' } });
  }
}));

export default router;
