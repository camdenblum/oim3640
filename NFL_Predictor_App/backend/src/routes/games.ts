import { Router } from 'express';
import { asyncHandler } from '../middleware/errorHandler';
import { GamesService } from '../services/gamesService';
import { cacheGet, cacheSet } from '../config/redis';

const router = Router();
const svc = new GamesService();

router.get('/', asyncHandler(async (req, res) => {
  const { season, week, team, status } = req.query;
  const data = await svc.getGames({
    season: season ? Number(season) : undefined,
    week: week ? Number(week) : undefined,
    teamId: team ? Number(team) : undefined,
    status: status as string,
  });
  res.json({ success: true, data });
}));

router.get('/upcoming', asyncHandler(async (req, res) => {
  const cacheKey = 'games:upcoming';
  const cached = await cacheGet(cacheKey);
  if (cached) { res.json({ success: true, data: cached }); return; }
  const data = await svc.getUpcomingGames();
  await cacheSet(cacheKey, data, 1800);
  res.json({ success: true, data });
}));

router.get('/live', asyncHandler(async (req, res) => {
  const data = await svc.getLiveGames();
  res.json({ success: true, data });
}));

router.get('/:id', asyncHandler(async (req, res) => {
  const data = await svc.getGameById(Number(req.params.id));
  res.json({ success: true, data });
}));

router.get('/:id/box-score', asyncHandler(async (req, res) => {
  const data = await svc.getBoxScore(Number(req.params.id));
  res.json({ success: true, data });
}));

router.get('/:id/play-by-play', asyncHandler(async (req, res) => {
  const data = await svc.getPlayByPlay(Number(req.params.id));
  res.json({ success: true, data });
}));

router.get('/:id/drives', asyncHandler(async (req, res) => {
  const data = await svc.getDrives(Number(req.params.id));
  res.json({ success: true, data });
}));

export default router;
