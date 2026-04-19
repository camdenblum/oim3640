import { Router } from 'express';
import { asyncHandler } from '../middleware/errorHandler';
import { PlayersService } from '../services/playersService';

const router = Router();
const svc = new PlayersService();

router.get('/', asyncHandler(async (req, res) => {
  const { team, position, status, page = '1', limit = '50' } = req.query;
  const data = await svc.getPlayers({
    teamId: team ? Number(team) : undefined,
    position: position as string,
    status: status as string,
    page: Number(page),
    limit: Number(limit),
  });
  res.json({ success: true, data });
}));

router.get('/search', asyncHandler(async (req, res) => {
  const data = await svc.searchPlayers(String(req.query.q || ''));
  res.json({ success: true, data });
}));

router.get('/leaderboards', asyncHandler(async (req, res) => {
  const data = await svc.getLeaderboards(
    String(req.query.stat || 'qb_yards'),
    String(req.query.position || 'QB'),
    Number(req.query.season),
    Number(req.query.week)
  );
  res.json({ success: true, data });
}));

router.get('/:id', asyncHandler(async (req, res) => {
  const data = await svc.getPlayerById(Number(req.params.id));
  res.json({ success: true, data });
}));

router.get('/:id/stats', asyncHandler(async (req, res) => {
  const data = await svc.getPlayerStats(Number(req.params.id), Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/:id/game-log', asyncHandler(async (req, res) => {
  const data = await svc.getPlayerGameLog(Number(req.params.id), Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/:id/trends', asyncHandler(async (req, res) => {
  const data = await svc.getPlayerTrends(Number(req.params.id));
  res.json({ success: true, data });
}));

router.get('/:id/splits', asyncHandler(async (req, res) => {
  const data = await svc.getPlayerSplits(Number(req.params.id), Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/:id/advanced', asyncHandler(async (req, res) => {
  const data = await svc.getPlayerAdvanced(Number(req.params.id));
  res.json({ success: true, data });
}));

router.get('/:id/snap-counts', asyncHandler(async (req, res) => {
  const data = await svc.getPlayerSnapCounts(Number(req.params.id), Number(req.query.season));
  res.json({ success: true, data });
}));

router.get('/:id/matchup-history', asyncHandler(async (req, res) => {
  const data = await svc.getPlayerMatchupHistory(Number(req.params.id), Number(req.query.opponentId));
  res.json({ success: true, data });
}));

export default router;
