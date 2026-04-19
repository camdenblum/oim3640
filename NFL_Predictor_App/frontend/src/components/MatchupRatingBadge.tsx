import { getMatchupRatingBg, getMatchupRatingColor } from '../utils/stats';

export default function MatchupRatingBadge({ rating }: { rating: number }) {
  const label = rating >= 67 ? 'Favorable' : rating >= 34 ? 'Neutral' : 'Tough';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-medium ${getMatchupRatingBg(rating)}`}>
      <span className={getMatchupRatingColor(rating)}>{rating.toFixed(0)}</span>
      <span className="text-gray-400">{label}</span>
    </span>
  );
}
