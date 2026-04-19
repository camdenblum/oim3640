import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { endpoints } from '../utils/api';
import WinProbabilityBar from '../components/WinProbabilityBar';
import MatchupRatingBadge from '../components/MatchupRatingBadge';
import InjuryStatusBadge from '../components/InjuryStatusBadge';
import { Skeleton, CardSkeleton } from '../components/LoadingSkeleton';
import { formatRecord } from '../utils/stats';
import { TeamLogo } from '../components/GamePredictionCard';

export default function GamePredictionPage() {
  const { id } = useParams<{ id: string }>();
  const gameId = Number(id);

  const { data: gameRes, isLoading: gameLoading } = useQuery({
    queryKey: ['game', gameId],
    queryFn: () => endpoints.games.byId(gameId),
  });

  const { data: predRes, isLoading: predLoading } = useQuery({
    queryKey: ['prediction', gameId],
    queryFn: () => endpoints.predictions.gameById(gameId),
  });

  const { data: playersRes } = useQuery({
    queryKey: ['game-players', gameId],
    queryFn: () => endpoints.predictions.gamePlayers(gameId),
  });

  const { data: injuryHomeRes } = useQuery({
    queryKey: ['injuries', gameRes?.data?.home_team_id],
    queryFn: () => endpoints.teams.injuries(gameRes?.data?.home_team_id),
    enabled: !!gameRes?.data?.home_team_id,
  });

  const game = gameRes?.data;
  const pred = predRes?.data;
  const playerProjections: any[] = playersRes?.data || [];
  const injuries: any[] = injuryHomeRes?.data || [];

  if (gameLoading) return <div className="space-y-4"><CardSkeleton /><CardSkeleton /></div>;
  if (!game) return <div className="card text-center text-gray-500">Game not found</div>;

  // Monte Carlo histogram
  const simDist: number[] = pred?.simulation_distribution || [];
  const histogramData = buildHistogram(simDist);

  return (
    <div className="space-y-8">
      {/* Section 1: Game Header */}
      <div className="card">
        <div className="grid grid-cols-3 items-center gap-6">
          <div className="flex flex-col items-center gap-2">
            <TeamLogo abbr={game.away_abbr} color={game.away_color} size="lg" />
            <div className="text-lg font-bold">{game.away_team_name}</div>
            <div className="text-sm text-gray-400">{game.away_abbr}</div>
          </div>
          <div className="text-center space-y-1">
            <div className="text-xs text-gray-400">{new Date(game.game_date).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}</div>
            <div className="text-xs text-gray-400">{new Date(game.game_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
            <div className="text-sm font-medium text-gray-300">{game.venue}</div>
            {game.broadcast_network && <div className="text-xs text-gray-500">{game.broadcast_network}</div>}
            {game.weather_temp_f && (
              <div className="text-xs text-blue-400">
                {game.weather_temp_f}°F · {game.weather_wind_mph}mph wind · {game.weather_conditions || 'Clear'}
              </div>
            )}
          </div>
          <div className="flex flex-col items-center gap-2">
            <TeamLogo abbr={game.home_abbr} color={game.home_color} size="lg" />
            <div className="text-lg font-bold">{game.home_team_name}</div>
            <div className="text-sm text-gray-400">{game.home_abbr} · HOME</div>
          </div>
        </div>
      </div>

      {/* Section 2: Win Probability */}
      {pred ? (
        <div className="card space-y-6">
          <h2 className="text-lg font-semibold">Win Probability & Score Prediction</h2>
          <WinProbabilityBar
            homeTeam={game.home_team_name} awayTeam={game.away_team_name}
            homeProb={pred.home_win_probability} awayProb={pred.away_win_probability}
            homeColor={game.home_color} awayColor={game.away_color} size="lg" />
          <div className="text-center">
            <div className="text-4xl font-black tracking-tight">
              <span style={{ color: game.away_color }}>{game.away_abbr}</span>
              <span className="text-gray-400 mx-4">{pred.predicted_away_score.toFixed(0)} — {pred.predicted_home_score.toFixed(0)}</span>
              <span style={{ color: game.home_color }}>{game.home_abbr}</span>
            </div>
            <div className="text-gray-400 text-sm mt-1">Predicted Score (ML Model)</div>
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xl font-bold">{pred.predicted_total_points.toFixed(1)}</div>
              <div className="text-xs text-gray-400">Total Points (O/U)</div>
            </div>
            <div>
              <div className={`text-xl font-bold ${pred.confidence_score > 0.7 ? 'text-green-400' : pred.confidence_score > 0.55 ? 'text-yellow-400' : 'text-gray-300'}`}>
                {(pred.confidence_score * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-400">Confidence</div>
            </div>
            <div>
              <div className="text-xl font-bold">
                {pred.predicted_spread > 0 ? `${game.home_abbr} -${pred.predicted_spread.toFixed(1)}` : `${game.away_abbr} -${Math.abs(pred.predicted_spread).toFixed(1)}`}
              </div>
              <div className="text-xs text-gray-400">Predicted Spread</div>
            </div>
          </div>

          {/* Monte Carlo */}
          {histogramData.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-2">Score Distribution (10,000 Simulations)</h3>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={histogramData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="total" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(v: number) => [`${v} sims`, 'Frequency']} labelFormatter={(l) => `Total: ${l} pts`} />
                  <Bar dataKey="count" fill="#013369" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      ) : predLoading ? <CardSkeleton /> : null}

      {/* Section 3: Key Matchup Factors */}
      {pred?.key_factors?.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Key Matchup Factors</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {pred.key_factors.map((factor: any, i: number) => (
              <div key={i} className="bg-gray-800/40 rounded-lg p-3 border border-nfl-border">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-gray-300">{factor.factor}</span>
                  <span className={`text-xs badge ${factor.favoredTeam === 'home' ? 'bg-blue-900 text-blue-300' : factor.favoredTeam === 'away' ? 'bg-red-900 text-red-300' : 'bg-gray-700 text-gray-300'}`}>
                    {factor.favoredTeam === 'home' ? game.home_abbr : factor.favoredTeam === 'away' ? game.away_abbr : 'Even'}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">{game.away_abbr}: <span className="text-white">{factor.awayValue}</span></span>
                  <span className="text-gray-400">{game.home_abbr}: <span className="text-white">{factor.homeValue}</span></span>
                </div>
                {factor.description && <p className="text-xs text-gray-500 mt-1">{factor.description}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 5: Player Projections */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Player Projections</h2>
        {playerProjections.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-nfl-border text-left text-xs text-gray-400">
                  <th className="pb-2 pr-4">Player</th>
                  <th className="pb-2 pr-4">Pos</th>
                  <th className="pb-2 pr-4">Team</th>
                  <th className="pb-2 pr-4">Matchup</th>
                  <th className="pb-2 pr-4">Proj Pts (PPR)</th>
                  <th className="pb-2">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nfl-border/50">
                {playerProjections.map((p: any, i: number) => (
                  <tr key={i} className="hover:bg-gray-800/20">
                    <td className="py-2 pr-4 font-medium">{p.full_name}</td>
                    <td className="py-2 pr-4 text-gray-400">{p.position}</td>
                    <td className="py-2 pr-4 text-gray-400">{p.team_abbr}</td>
                    <td className="py-2 pr-4"><MatchupRatingBadge rating={p.matchup_rating || 50} /></td>
                    <td className="py-2 pr-4 font-semibold text-nfl-gold">{p.projected_fantasy_ppr?.toFixed(1) || '—'}</td>
                    <td className="py-2 text-gray-400">{((p.confidence_score || 0.5) * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Player projections will appear once the analytics service processes this game.</p>
        )}
      </div>

      {/* Section 6: Injury Reports */}
      {injuries.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-3">Injury Report</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {injuries.map((p: any) => (
              <div key={p.id} className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/30">
                <div className="flex-1">
                  <div className="text-sm font-medium">{p.full_name}</div>
                  <div className="text-xs text-gray-400">{p.position} · {p.injury_description}</div>
                </div>
                <InjuryStatusBadge status={p.injury_status} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function buildHistogram(scores: number[]): { total: number; count: number }[] {
  if (!scores.length) return [];
  const counts: Record<number, number> = {};
  for (const s of scores) {
    const bucket = Math.round(s / 4) * 4;
    counts[bucket] = (counts[bucket] || 0) + 1;
  }
  return Object.entries(counts)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([total, count]) => ({ total: Number(total), count }));
}
