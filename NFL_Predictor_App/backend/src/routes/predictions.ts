import { Router } from 'express';
import { asyncHandler } from '../middleware/errorHandler';
import { PredictionsService } from '../services/predictionsService';
import { cacheGet, cacheSet } from '../config/redis';

const router = Router();
const svc = new PredictionsService();

router.get('/games', asyncHandler(async (req, res) => {
  const cacheKey = `predictions:games:week${req.query.week || 'current'}`;
  const cached = await cacheGet(cacheKey);
  if (cached) { res.json({ success: true, data: cached }); return; }
  const data = await svc.getWeekPredictions(Number(req.query.week));
  await cacheSet(cacheKey, data, 900);
  res.json({ success: true, data });
}));

router.get('/games/:gameId', asyncHandler(async (req, res) => {
  const data = await svc.getGamePrediction(Number(req.params.gameId));
  res.json({ success: true, data });
}));

router.get('/games/:gameId/players', asyncHandler(async (req, res) => {
  const data = await svc.getGamePlayerProjections(Number(req.params.gameId));
  res.json({ success: true, data });
}));

router.get('/players/:playerId', asyncHandler(async (req, res) => {
  const data = await svc.getPlayerProjection(Number(req.params.playerId));
  res.json({ success: true, data });
}));

router.get('/season/:teamId', asyncHandler(async (req, res) => {
  const data = await svc.getSeasonProjection(Number(req.params.teamId));
  res.json({ success: true, data });
}));

router.get('/playoffs', asyncHandler(async (req, res) => {
  const data = await svc.getPlayoffProbabilities();
  res.json({ success: true, data });
}));

router.post('/simulate', asyncHandler(async (req, res) => {
  const { homeTeamId, awayTeamId, weekContext } = req.body;
  const data = await svc.simulateGame(homeTeamId, awayTeamId, weekContext);
  res.json({ success: true, data });
}));

router.get('/accuracy', asyncHandler(async (req, res) => {
  const data = await svc.getModelAccuracy();
  res.json({ success: true, data });
}));

router.get('/leaderboard', asyncHandler(async (req, res) => {
  const data = await svc.getPredictionLeaderboard(Number(req.query.week));
  res.json({ success: true, data });
}));

export default router;
