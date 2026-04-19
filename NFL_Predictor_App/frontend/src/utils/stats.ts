/** NFL statistical calculation helpers — mirroring the Python analytics formulas */

export function passerRating(comp: number, att: number, yards: number, td: number, int_: number): number {
  if (att === 0) return 0;
  const a = Math.max(0, Math.min(((comp / att) - 0.3) * 5, 2.375));
  const b = Math.max(0, Math.min(((yards / att) - 3) * 0.25, 2.375));
  const c = Math.max(0, Math.min((td / att) * 20, 2.375));
  const d = Math.max(0, Math.min(2.375 - ((int_ / att) * 25), 2.375));
  return parseFloat(((a + b + c + d) / 6 * 100).toFixed(1));
}

export function fantasyPointsStd(stats: Record<string, number>, position: string): number {
  let pts = 0;
  if (position === 'QB') {
    pts += (stats.qb_yards || 0) * 0.04;
    pts += (stats.qb_touchdowns || 0) * 4;
    pts -= (stats.qb_interceptions || 0) * 2;
    pts += (stats.rb_yards || 0) * 0.1;
    pts += (stats.rb_touchdowns || 0) * 6;
  } else if (position === 'RB') {
    pts += (stats.rb_yards || 0) * 0.1;
    pts += (stats.rb_touchdowns || 0) * 6;
    pts += (stats.rec_yards || 0) * 0.1;
    pts += (stats.rec_touchdowns || 0) * 6;
  } else if (['WR', 'TE'].includes(position)) {
    pts += (stats.rec_yards || 0) * 0.1;
    pts += (stats.rec_touchdowns || 0) * 6;
  } else if (['DEF', 'LB', 'DL', 'CB', 'S'].includes(position)) {
    pts += (stats.def_sacks || 0) * 1;
    pts += (stats.def_interceptions || 0) * 2;
    pts += (stats.def_tackles || 0) * 0.5;
  }
  return Math.max(0, parseFloat(pts.toFixed(1)));
}

export function fantasyPointsPPR(stats: Record<string, number>, position: string): number {
  return parseFloat((fantasyPointsStd(stats, position) + (stats.rec_receptions || stats.receptions || 0)).toFixed(1));
}

export function successRate(conversions: number, attempts: number): number {
  if (!attempts) return 0;
  return parseFloat((conversions / attempts * 100).toFixed(1));
}

export function formatRecord(wins: number, losses: number, ties = 0): string {
  return ties ? `${wins}-${losses}-${ties}` : `${wins}-${losses}`;
}

export function ordinalRank(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

export function getRankColor(rank: number, total = 32): string {
  const pct = rank / total;
  if (pct <= 0.25) return 'text-green-400';
  if (pct <= 0.5) return 'text-yellow-400';
  if (pct <= 0.75) return 'text-orange-400';
  return 'text-red-400';
}

export function getInjuryStatusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case 'active': return 'text-green-400 bg-green-900/30';
    case 'questionable': return 'text-yellow-400 bg-yellow-900/30';
    case 'doubtful': return 'text-orange-400 bg-orange-900/30';
    case 'out': return 'text-red-400 bg-red-900/30';
    case 'injured reserve': case 'ir': return 'text-red-600 bg-red-900/50';
    case 'pup': return 'text-gray-400 bg-gray-700/30';
    default: return 'text-gray-400 bg-gray-700/30';
  }
}

export function getMatchupRatingColor(rating: number): string {
  if (rating >= 67) return 'text-green-400';
  if (rating >= 34) return 'text-yellow-400';
  return 'text-red-400';
}

export function getMatchupRatingBg(rating: number): string {
  if (rating >= 67) return 'bg-green-900/40 border-green-700/50';
  if (rating >= 34) return 'bg-yellow-900/40 border-yellow-700/50';
  return 'bg-red-900/40 border-red-700/50';
}

export function formatStat(value: number | null | undefined, decimals = 0): string {
  if (value == null || isNaN(value)) return '—';
  return value.toFixed(decimals);
}

export function computeWinPct(wins: number, losses: number, ties = 0): number {
  const games = wins + losses + ties;
  if (!games) return 0;
  return (wins + ties * 0.5) / games;
}
