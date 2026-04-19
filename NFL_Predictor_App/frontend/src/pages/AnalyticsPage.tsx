import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar } from 'recharts';
import { endpoints } from '../utils/api';
import { useAppStore } from '../store/appStore';
import { Skeleton } from '../components/LoadingSkeleton';
import { downloadCSV } from '../utils/csv';

export default function AnalyticsPage() {
  const { currentSeason } = useAppStore();
  const [tab, setTab] = useState<'standings' | 'trends' | 'schedule'>('standings');

  const { data: standingsRes, isLoading } = useQuery({
    queryKey: ['standings', currentSeason],
    queryFn: () => endpoints.analytics.standings(currentSeason),
  });

  const { data: trendsRes } = useQuery({
    queryKey: ['trends', currentSeason],
    queryFn: () => endpoints.analytics.trends(currentSeason),
    enabled: tab === 'trends',
  });

  const { data: scheduleRes } = useQuery({
    queryKey: ['schedule-difficulty'],
    queryFn: () => endpoints.analytics.scheduleDifficulty(),
    enabled: tab === 'schedule',
  });

  const standings: any[] = standingsRes?.data || [];
  const trends: any[] = trendsRes?.data || [];
  const scheduleDiff: any[] = scheduleRes?.data || [];

  const afc = standings.filter(t => t.conference === 'AFC');
  const nfc = standings.filter(t => t.conference === 'NFC');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-gray-400 text-sm">{currentSeason} NFL Season</p>
        </div>
        <div className="flex items-center gap-2">
          {tab === 'standings' && standings.length > 0 && (
            <button onClick={() => downloadCSV(
              standings.map((t: any) => ({
                Team: `${t.city} ${t.name}`, Conf: t.conference, Div: t.division,
                W: t.wins, L: t.losses, T: t.ties,
                PF: t.points_for, PA: t.points_against,
              })),
              `nfl-standings-${currentSeason}`
            )} className="btn-ghost text-xs">↓ CSV</button>
          )}
          {tab === 'schedule' && scheduleDiff.length > 0 && (
            <button onClick={() => downloadCSV(
              [...scheduleDiff].sort((a: any, b: any) => b.avg_remaining_opp_elo - a.avg_remaining_opp_elo).map((t: any) => ({
                Team: t.abbreviation,
                Remaining: t.remaining_games,
                AvgOppElo: Number(t.avg_remaining_opp_elo || 1500).toFixed(0),
              })),
              `nfl-schedule-difficulty-${currentSeason}`
            )} className="btn-ghost text-xs">↓ CSV</button>
          )}
          <Link to="/analytics/power-rankings" className="btn-primary text-sm">Power Rankings →</Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-nfl-border">
        {[['standings', 'Standings'], ['trends', 'League Trends'], ['schedule', 'Schedule Difficulty']].map(([v, label]) => (
          <button key={v} onClick={() => setTab(v as any)}
            className={`px-4 py-2 text-sm font-medium ${tab === v ? 'tab-active' : 'tab-inactive'}`}>
            {label}
          </button>
        ))}
      </div>

      {/* Standings */}
      {tab === 'standings' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[['AFC', afc], ['NFC', nfc]].map(([conf, teams]: any) => (
            <div key={conf} className="card">
              <h2 className="text-lg font-semibold text-nfl-gold mb-4">{conf}</h2>
              {isLoading ? <Skeleton className="h-48 w-full" /> : (
                <div className="divide-y divide-nfl-border">
                  {teams.map((team: any, i: number) => (
                    <div key={team.id} className="flex items-center gap-3 py-2.5">
                      <span className="w-5 text-xs text-gray-500">{i + 1}</span>
                      <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white"
                        style={{ backgroundColor: team.primary_color }}>
                        {team.abbreviation?.slice(0, 2)}
                      </div>
                      <Link to={`/teams/${team.id}`} className="flex-1 text-sm font-medium hover:text-nfl-gold">
                        {team.city} {team.name}
                      </Link>
                      <span className="font-bold text-sm">{team.wins}–{team.losses}{team.ties > 0 ? `–${team.ties}` : ''}</span>
                      <span className="text-xs text-gray-400 w-16 text-right">
                        {team.points_for}–{team.points_against}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* League Trends */}
      {tab === 'trends' && (
        <div className="space-y-6">
          {trends.length > 0 ? (
            <>
              <div className="card">
                <h3 className="text-sm font-medium text-gray-400 mb-3">Points Per Game — League Average by Week</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={trends}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                    <XAxis dataKey="week" tick={{ fontSize: 10 }} label={{ value: 'Week', position: 'bottom', fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} domain={[14, 32]} />
                    <Tooltip formatter={(v: number) => [v.toFixed(1), 'Avg PPG']} />
                    <Line type="monotone" dataKey="avg_ppg" stroke="#FFB612" strokeWidth={2} dot={{ r: 3 }} name="PPG" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="card">
                  <h3 className="text-sm font-medium text-gray-400 mb-3">Pass vs Rush Yards by Week</h3>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={trends}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                      <XAxis dataKey="week" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Bar dataKey="avg_pass_yards" fill="#013369" name="Pass Yds" radius={[2, 2, 0, 0]} />
                      <Bar dataKey="avg_rush_yards" fill="#D50A0A" name="Rush Yds" radius={[2, 2, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="card">
                  <h3 className="text-sm font-medium text-gray-400 mb-3">Pass Rate Trend</h3>
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={trends}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                      <XAxis dataKey="week" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                      <Tooltip formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, 'Pass Rate']} />
                      <Line type="monotone" dataKey="pass_rate" stroke="#4ade80" strokeWidth={2} dot={{ r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          ) : (
            <div className="card text-center text-gray-500 py-12">
              <p>League trend data becomes available after Week 2.</p>
            </div>
          )}
        </div>
      )}

      {/* Schedule Difficulty */}
      {tab === 'schedule' && (
        <div className="card overflow-x-auto">
          <h2 className="text-lg font-semibold mb-4">Remaining Schedule Difficulty</h2>
          {scheduleDiff.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-nfl-border text-left text-xs text-gray-400">
                  <th className="pb-2 pr-4">Team</th>
                  <th className="pb-2 pr-4">Remaining Games</th>
                  <th className="pb-2 pr-4">Avg Opp Elo</th>
                  <th className="pb-2">Difficulty</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nfl-border/30">
                {scheduleDiff.sort((a: any, b: any) => b.avg_remaining_opp_elo - a.avg_remaining_opp_elo).map((t: any) => {
                  const elo = Number(t.avg_remaining_opp_elo || 1500);
                  const diff = elo - 1500;
                  return (
                    <tr key={t.id} className="hover:bg-gray-800/20">
                      <td className="py-2.5 pr-4">
                        <Link to={`/teams/${t.id}`} className="font-medium hover:text-nfl-gold">{t.abbreviation}</Link>
                      </td>
                      <td className="py-2.5 pr-4 text-gray-400">{t.remaining_games}</td>
                      <td className="py-2.5 pr-4">{elo.toFixed(0)}</td>
                      <td className="py-2.5">
                        <span className={`badge ${diff > 50 ? 'bg-red-900 text-red-300' : diff > 0 ? 'bg-yellow-900 text-yellow-300' : 'bg-green-900 text-green-300'}`}>
                          {diff > 50 ? 'Hard' : diff > 0 ? 'Average' : 'Easy'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <p className="text-center text-gray-500 py-8">Schedule difficulty data not yet available.</p>
          )}
        </div>
      )}
    </div>
  );
}
