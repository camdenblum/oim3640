import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { endpoints } from '../utils/api';
import GamePredictionCard from '../components/GamePredictionCard';
import { GameCardSkeleton } from '../components/LoadingSkeleton';

export default function PredictionsPage() {
  const { currentWeek, setWeek } = useAppStore();

  const { data: gamesRes, isLoading: gamesLoading } = useQuery({
    queryKey: ['games-upcoming', currentWeek],
    queryFn: () => endpoints.games.all({ week: currentWeek }),
  });

  const { data: predsRes, isLoading: predsLoading } = useQuery({
    queryKey: ['predictions', currentWeek],
    queryFn: () => endpoints.predictions.games(currentWeek),
  });

  const { data: leaderboardRes } = useQuery({
    queryKey: ['prediction-leaderboard', currentWeek],
    queryFn: () => endpoints.predictions.leaderboard(currentWeek),
  });

  const games: any[] = gamesRes?.data || [];
  const preds: any[] = predsRes?.data || [];
  const leaderboard: any[] = leaderboardRes?.data || [];
  const predMap = Object.fromEntries(preds.map((p: any) => [p.game_id, p]));

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Game Predictions</h1>
          <p className="text-gray-400 text-sm">ML-powered win probabilities and score forecasts</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setWeek(currentWeek - 1)} disabled={currentWeek <= 1}
            className="w-8 h-8 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-30 flex items-center justify-center">‹</button>
          <span className="px-4 py-1.5 bg-nfl-blue rounded-full text-sm font-medium">Week {currentWeek}</span>
          <button onClick={() => setWeek(currentWeek + 1)} disabled={currentWeek >= 18}
            className="w-8 h-8 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-30 flex items-center justify-center">›</button>
        </div>
      </div>

      {/* Nav links */}
      <div className="flex gap-3">
        <Link to="/predict/players" className="btn bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm">
          Player Projections →
        </Link>
        <Link to="/predict/season" className="btn bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm">
          Season Projections →
        </Link>
      </div>

      {/* Game Cards */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Week {currentWeek} Predictions</h2>
        {gamesLoading || predsLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => <GameCardSkeleton key={i} />)}
          </div>
        ) : games.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {games.map((game: any) => (
              <GamePredictionCard key={game.id} game={game} prediction={predMap[game.id]} />
            ))}
          </div>
        ) : (
          <div className="card text-center text-gray-500 py-12">
            <p>No predictions yet for Week {currentWeek}.</p>
            <p className="text-xs mt-2">Predictions generate every Wednesday from live ESPN + NFLverse data.</p>
          </div>
        )}
      </section>

      {/* Top Projected Performers */}
      {leaderboard.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Top Projected Performers</h2>
            <Link to="/predict/players" className="text-sm text-nfl-gold hover:underline">Full list →</Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {leaderboard.slice(0, 8).map((p: any, i: number) => (
              <Link key={p.player_id || i} to={`/players/${p.player_id}`} className="card-hover">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center font-bold text-sm">
                    {p.position?.slice(0, 2)}
                  </div>
                  <div>
                    <div className="font-semibold text-sm">{p.full_name}</div>
                    <div className="text-xs text-gray-400">{p.team_abbr} · {p.position}</div>
                  </div>
                </div>
                <div className="flex justify-between items-end">
                  <div>
                    <div className="text-xl font-bold text-nfl-gold">{p.projected_fantasy_ppr?.toFixed(1) || '—'}</div>
                    <div className="text-xs text-gray-500">PPR Pts</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">{p.matchup_rating?.toFixed(0) || 50}/100</div>
                    <div className="text-xs text-gray-500">Matchup</div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
