import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ScatterChart, Scatter } from 'recharts';
import { endpoints } from '../utils/api';
import { api } from '../utils/api';
import { Skeleton } from '../components/LoadingSkeleton';

export default function ModelPage() {
  const { data: accuracyRes, isLoading } = useQuery({
    queryKey: ['model-accuracy'],
    queryFn: () => endpoints.predictions.accuracy(),
  });

  const { data: featureRes } = useQuery({
    queryKey: ['feature-importance'],
    queryFn: () => api.get('/analytics/feature-importance'),
    retry: false,
  });

  const accuracy: any[] = accuracyRes?.data || [];
  const features: any[] = (featureRes as any)?.importance || [];
  const latestModel = accuracy[0];

  const calibrationData = accuracy.map((m: any) => ({
    predicted: Math.round(m.avg_predicted * 100) / 100 || 0.5,
    actual: Math.round(m.accuracy * 100) / 100 || 0.5,
    games: m.games_evaluated || 0,
  }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Model Performance Dashboard</h1>
        <p className="text-gray-400 text-sm mt-1">Transparency into the prediction engine</p>
      </div>

      {/* Overall Accuracy Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {isLoading ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 w-full" />) : (
          <>
            <MetricCard
              label="Win/Loss Accuracy"
              value={latestModel ? `${(latestModel.accuracy * 100).toFixed(1)}%` : '—'}
              subtitle={`${latestModel?.games_evaluated || 0} games evaluated`}
              color={latestModel?.accuracy > 0.6 ? 'text-green-400' : 'text-yellow-400'}
            />
            <MetricCard
              label="Score MAE"
              value={latestModel ? `${Number(latestModel.mae || 0).toFixed(1)} pts` : '—'}
              subtitle="Mean absolute error"
              color="text-blue-400"
            />
            <MetricCard
              label="Model Version"
              value={latestModel?.model_version || 'elo-fallback'}
              subtitle="Current active model"
              color="text-nfl-gold"
            />
            <MetricCard
              label="Total Predictions"
              value={latestModel?.total_predictions || 0}
              subtitle="Season to date"
              color="text-purple-400"
            />
          </>
        )}
      </div>

      {/* Model Version History */}
      {accuracy.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Model Version History</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-nfl-border text-left text-xs text-gray-400">
                  <th className="pb-2 pr-4">Version</th>
                  <th className="pb-2 pr-4">Win Accuracy</th>
                  <th className="pb-2 pr-4">Score MAE</th>
                  <th className="pb-2 pr-4">Games</th>
                  <th className="pb-2">Predictions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nfl-border/30">
                {accuracy.map((m: any, i: number) => (
                  <tr key={i} className={`hover:bg-gray-800/20 ${i === 0 ? 'bg-nfl-blue/10' : ''}`}>
                    <td className="py-2.5 pr-4">
                      <span className="font-mono text-xs">{m.model_version}</span>
                      {i === 0 && <span className="ml-2 badge bg-green-900/50 text-green-300 text-xs">Active</span>}
                    </td>
                    <td className="py-2.5 pr-4">
                      <span className={Number(m.accuracy || 0) > 0.6 ? 'text-green-400 font-semibold' : 'text-yellow-400'}>
                        {(Number(m.accuracy || 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 pr-4">{Number(m.mae || 0).toFixed(1)} pts</td>
                    <td className="py-2.5 pr-4">{m.games_evaluated}</td>
                    <td className="py-2.5">{m.total_predictions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Feature Importance */}
      {features.length > 0 ? (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Feature Importance (Top 20)</h2>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={features.slice(0, 20)} layout="vertical" margin={{ left: 120, right: 20, top: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363d" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={v => v.toFixed(3)} />
              <YAxis type="category" dataKey="feature" tick={{ fontSize: 10 }} width={115} />
              <Tooltip formatter={(v: number) => [v.toFixed(4), 'Importance']} />
              <Bar dataKey="importance" fill="#013369" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="card text-center text-gray-500 py-8">
          <p className="text-lg">Feature importance shows after the ML model is trained.</p>
          <p className="text-sm mt-2">The Elo fallback model is used until enough game data is collected (≥50 games).</p>
          <p className="text-xs mt-1 text-gray-600">Training triggers automatically every Tuesday morning via cron job.</p>
        </div>
      )}

      {/* Model Info */}
      <div className="card space-y-4 text-sm text-gray-300">
        <h2 className="text-lg font-semibold text-white">Model Architecture</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { title: 'Elo System', desc: 'Baseline win probability. K=20, home field = +65 Elo pts. Updates after every game using margin-of-victory multiplier (FiveThirtyEight method).', icon: '📊' },
            { title: 'XGBoost Classifier', desc: '70+ features covering team efficiency, EPA, situational stats, injury flags, weather, rest, and head-to-head history. Walk-forward cross-validation prevents data leakage.', icon: '🌲' },
            { title: 'Score Regressor', desc: 'Separate XGBoost model predicts final score for each team. Combined with 10,000 Monte Carlo simulations for score distribution.', icon: '🎯' },
          ].map(({ title, desc, icon }) => (
            <div key={title} className="bg-gray-800/40 rounded-lg p-4 border border-nfl-border">
              <div className="text-2xl mb-2">{icon}</div>
              <div className="font-semibold text-white mb-1">{title}</div>
              <p className="text-xs text-gray-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
        <div className="bg-gray-800/30 rounded-lg p-4 border border-nfl-border/50 text-xs text-gray-400 space-y-1">
          <p><span className="text-white">Data Sources:</span> ESPN Public API (real-time), NFLverse GitHub (play-by-play, EPA, snap counts), Pro Football Reference (scraped), OpenWeatherMap (outdoor stadiums), The Odds API (implied totals)</p>
          <p><span className="text-white">Retraining:</span> Every Tuesday at 6am via cron job, using walk-forward validation on all completed games of the current season</p>
          <p><span className="text-white">Fallback:</span> When model is not yet trained (start of season / &lt;50 games), Elo-only predictions are served with lower confidence scores</p>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, subtitle, color }: any) {
  return (
    <div className="card">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-gray-400 mt-1 uppercase tracking-wide">{label}</div>
      {subtitle && <div className="text-xs text-gray-500 mt-0.5">{subtitle}</div>}
    </div>
  );
}
