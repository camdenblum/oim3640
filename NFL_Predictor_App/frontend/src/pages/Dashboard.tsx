import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { endpoints } from '../utils/api';
import GamePredictionCard from '../components/GamePredictionCard';
import StatCard from '../components/StatCard';
import { GameCardSkeleton, Skeleton } from '../components/LoadingSkeleton';
import WinProbabilityBar from '../components/WinProbabilityBar';
import { formatRecord } from '../utils/stats';

export default function Dashboard() {
  const { currentWeek, currentSeason, setWeek } = useAppStore();

  const { data: gamesRes, isLoading: gamesLoading } = useQuery({
    queryKey: ['games', currentSeason, currentWeek],
    queryFn: () => endpoints.games.all({ season: currentSeason, week: currentWeek }),
  });

  const { data: predictionsRes, isLoading: predsLoading } = useQuery({
    queryKey: ['predictions', currentWeek],
    queryFn: () => endpoints.predictions.games(currentWeek),
  });

  const { data: powerRes } = useQuery({
    queryKey: ['power-rankings', currentWeek],
    queryFn: () => endpoints.analytics.powerRankings(currentWeek),
  });

  const { data: leaderboardRes } = useQuery({
    queryKey: ['prediction-leaderboard', currentWeek],
    queryFn: () => endpoints.predictions.leaderboard(currentWeek),
  });

  const { data: accuracyRes } = useQuery({
    queryKey: ['model-accuracy'],
    queryFn: () => endpoints.predictions.accuracy(),
  });

  const games: any[] = gamesRes?.data || [];
  const predictions: any[] = predictionsRes?.data || [];
  const powerRankings: any[] = powerRes?.data || [];
  const leaderboard: any[] = leaderboardRes?.data || [];
  const accuracy: any[] = accuracyRes?.data || [];

  const featuredGame = games[0];
  const featuredPrediction = predictions.find((p: any) => p.game_id === featuredGame?.id);

  // Map predictions by game ID
  const predMap = Object.fromEntries(predictions.map((p: any) => [p.game_id, p]));

  const latestAccuracy = accuracy[0];

  return (
    <div className="space-y-8">
      {/* Week selector */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">NFL Predictions</h1>
          <p className="text-gray-400 text-sm">{currentSeason} Season</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setWeek(currentWeek - 1)} disabled={currentWeek <= 1}
            className="w-8 h-8 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-30 flex items-center justify-center">‹</button>
          <div className="px-4 py-1.5 bg-nfl-blue rounded-full text-sm font-medium">Week {currentWeek}</div>
          <button onClick={() => setWeek(currentWeek + 1)} disabled={currentWeek >= 18}
            className="w-8 h-8 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-30 flex items-center justify-center">›</button>
        </div>
      </div>

      {/* Featured Game */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Featured Game</h2>
        {gamesLoading ? <GameCardSkeleton /> : featuredGame ? (
          <GamePredictionCard game={featuredGame} prediction={featuredPrediction} variant="featured" />
        ) : (
          <div className="card text-center text-gray-500">No games scheduled for Week {currentWeek}</div>
        )}
      </section>

      {/* Games Grid */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Week {currentWeek} Games</h2>
        {gamesLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => <GameCardSkeleton key={i} />)}
          </div>
        ) : games.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {games.slice(1).map((game: any) => (
              <GamePredictionCard key={game.id} game={game} prediction={predMap[game.id]} />
            ))}
          </div>
        ) : (
          <div className="card text-center text-gray-500 py-8">No games found for this week. Data syncs automatically.</div>
        )}
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top Player Projections */}
        <section className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Top Projections This Week</h2>
            <Link to="/predict/players" className="text-sm text-nfl-gold hover:underline">View all →</Link>
          </div>
          <div className="card">
            {leaderboard.length > 0 ? (
              <div className="divide-y divide-nfl-border">
                {leaderboard.slice(0, 10).map((item: any, i: number) => (
                  <Link key={item.player_id || i} to={`/players/${item.player_id}`}
                    className="flex items-center gap-3 py-3 hover:bg-gray-800/30 px-2 rounded-lg transition-colors">
                    <span className="w-6 text-gray-500 text-sm font-mono">{i + 1}</span>
                    <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold"
                      style={{ backgroundColor: item.primary_color }}>
                      {item.position?.slice(0, 2)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{item.full_name}</div>
                      <div className="text-xs text-gray-500">{item.team_abbr} · {item.position}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-nfl-gold">{item.projected_fantasy_ppr?.toFixed(1) || '—'} pts</div>
                      <div className="text-xs text-gray-500">PPR</div>
                    </div>
                    <div className="w-16 bg-gray-700 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-nfl-gold"
                        style={{ width: `${Math.min(100, (item.matchup_rating || 50))}%` }} />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <p>Player projections generate once game data is synced.</p>
                <p className="text-xs mt-1">Check back after initial data load completes.</p>
              </div>
            )}
          </div>
        </section>

        {/* Power Rankings + Model Accuracy */}
        <section className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold">Power Rankings</h2>
              <Link to="/analytics/power-rankings" className="text-sm text-nfl-gold hover:underline">Full →</Link>
            </div>
            <div className="card divide-y divide-nfl-border">
              {powerRankings.slice(0, 10).map((team: any, i: number) => (
                <Link key={team.id} to={`/teams/${team.id}`}
                  className="flex items-center gap-3 py-2 hover:bg-gray-800/20 px-1 rounded transition-colors">
                  <span className="w-5 text-gray-500 text-xs font-mono text-right">{i + 1}</span>
                  <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white"
                    style={{ backgroundColor: team.primary_color || '#013369' }}>
                    {team.abbreviation?.slice(0, 1)}
                  </div>
                  <span className="flex-1 text-sm font-medium">{team.abbreviation}</span>
                  <span className="text-xs text-gray-400">{(team.elo || 1500).toFixed(0)}</span>
                </Link>
              ))}
            </div>
          </div>

          {/* Model Accuracy */}
          <div>
            <h2 className="text-lg font-semibold mb-3">Model Accuracy</h2>
            <div className="card space-y-3">
              {latestAccuracy ? (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Win/Loss Accuracy</span>
                    <span className="text-lg font-bold text-green-400">
                      {(latestAccuracy.accuracy * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Score Error (MAE)</span>
                    <span className="font-medium">{Number(latestAccuracy.mae || 0).toFixed(1)} pts</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Games Evaluated</span>
                    <span className="font-medium">{latestAccuracy.games_evaluated || 0}</span>
                  </div>
                  <Link to="/model" className="block text-center text-xs text-nfl-gold hover:underline mt-2">
                    Full model dashboard →
                  </Link>
                </>
              ) : (
                <div className="text-center text-gray-500 text-sm py-2">
                  <p>Accuracy metrics populate after predictions are evaluated.</p>
                  <Link to="/model" className="text-nfl-gold text-xs hover:underline">View model dashboard →</Link>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
