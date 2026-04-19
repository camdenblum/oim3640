import { Router } from 'express';
import { asyncHandler } from '../middleware/errorHandler';
import { TeamsService } from '../services/teamsService';
import { cacheGet, cacheSet } from '../config/redis';

const router = Router();
const svc = new TeamsService();

router.get('/', asyncHandler(async (req, res) => {
  const cacheKey = `teams:all:${req.query.season || 'current'}`;
  const cached = await cacheGet(cacheKey);
  if (cached) { res.json({ success: true, data: cached }); return; }
  const data = await svc.getAllTeams(Number(req.query.season));
  await cacheSet(cacheKey, data, 3600);
  res.json({ success: true, data });
}));

router.get('/compare', asyncHandler(async (req, res) => {
  const ids = String(req.query.ids || '').split(',').map(Number).filter(Boolean);
  const data = await svc.compareTeams(ids);
  res.json({ success: true, data });
}));

router.get('/:id', asyncHandler(async (req, res) => {
  const data = await svc.getTeamById(Number(req.params.id));
  res.json({ success: true, data });
}));

router.get('/:id/stats', asyncHandler(async (req, res) => {
  const data = await svc.getTeamStats(Number(req.params.id), Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/:id/stats/weekly', asyncHandler(async (req, res) => {
  const data = await svc.getTeamWeeklyStats(Number(req.params.id), Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/:id/roster', asyncHandler(async (req, res) => {
  const cacheKey = `team:${req.params.id}:roster`;
  const cached = await cacheGet(cacheKey);
  if (cached) { res.json({ success: true, data: cached }); return; }
  const data = await svc.getTeamRoster(Number(req.params.id));
  await cacheSet(cacheKey, data, 1800);
  res.json({ success: true, data });
}));

router.get('/:id/schedule', asyncHandler(async (req, res) => {
  const data = await svc.getTeamSchedule(Number(req.params.id), Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/:id/splits', asyncHandler(async (req, res) => {
  const data = await svc.getTeamSplits(Number(req.params.id), Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/:id/situational', asyncHandler(async (req, res) => {
  const data = await svc.getTeamSituational(Number(req.params.id), Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/:id/advanced', asyncHandler(async (req, res) => {
  const data = await svc.getTeamAdvanced(Number(req.params.id), Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/:id/injuries', asyncHandler(async (req, res) => {
  const data = await svc.getTeamInjuries(Number(req.params.id));
  res.json({ success: true, data });
}));

export default router;
