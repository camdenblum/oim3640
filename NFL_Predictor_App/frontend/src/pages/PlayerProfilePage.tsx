import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, CartesianGrid } from 'recharts';
import { endpoints } from '../utils/api';
import InjuryStatusBadge from '../components/InjuryStatusBadge';
import MatchupRatingBadge from '../components/MatchupRatingBadge';
import { CardSkeleton, Skeleton } from '../components/LoadingSkeleton';
import { formatStat } from '../utils/stats';
import { downloadCSV } from '../utils/csv';

const TABS = ['Stats', 'Trends', 'Splits', 'Projections'];

export default function PlayerProfilePage() {
  const { id } = useParams<{ id: string }>();
  const playerId = Number(id);
  const [activeTab, setActiveTab] = useState(0);

  const { data: playerRes, isLoading } = useQuery({ queryKey: ['player', playerId], queryFn: () => endpoints.players.byId(playerId) });
  const { data: statsRes } = useQuery({ queryKey: ['player-stats', playerId], queryFn: () => endpoints.players.stats(playerId) });
  const { data: gameLogRes } = useQuery({ queryKey: ['player-gamelog', playerId], queryFn: () => endpoints.players.gameLog(playerId), enabled: activeTab === 0 });
  const { data: trendsRes } = useQuery({ queryKey: ['player-trends', playerId], queryFn: () => endpoints.players.trends(playerId), enabled: activeTab === 1 });
  const { data: splitsRes } = useQuery({ queryKey: ['player-splits', playerId], queryFn: () => endpoints.players.splits(playerId), enabled: activeTab === 2 });
  const { data: projectionRes } = useQuery({ queryKey: ['player-projection', playerId], queryFn: () => endpoints.predictions.player(playerId), enabled: activeTab === 3 });

  const player = playerRes?.data;
  const stats = statsRes?.data;
  const gameLog: any[] = gameLogRes?.data || [];
  const trends: any[] = trendsRes?.data || [];
  const splits = splitsRes?.data;
  const projection = projectionRes?.data;

  if (isLoading) return <div className="space-y-4"><Skeleton className="h-40 w-full" /><CardSkeleton /></div>;
  if (!player) return <div className="card text-center text-gray-500">Player not found</div>;

  const position = player.position;

  return (
    <div className="space-y-6">
      {/* Player Header */}
      <div className="card" style={{ borderLeftColor: player.primary_color, borderLeftWidth: 4 }}>
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-black text-white"
            style={{ backgroundColor: player.primary_color || '#1a1a2e' }}>
            {player.jersey_number || '?'}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{player.full_name}</h1>
              <InjuryStatusBadge status={player.injury_status} />
            </div>
            <div className="flex gap-3 text-sm text-gray-400 mt-1 flex-wrap">
              <span>{position}</span>
              {player.team_name && <Link to={`/teams/${player.team_id}`} className="hover:text-nfl-gold">{player.team_abbr}</Link>}
              {player.age && <span>{player.age} yrs</span>}
              {player.height_inches && <span>{Math.floor(player.height_inches / 12)}'{player.height_inches % 12}"</span>}
              {player.weight_lbs && <span>{player.weight_lbs} lbs</span>}
              {player.college && <span>{player.college}</span>}
            </div>
            {player.draft_year && (
              <div className="text-xs text-gray-500 mt-1">
                {player.draft_year} NFL Draft · Round {player.draft_round}, Pick {player.draft_pick}
              </div>
            )}
          </div>
          {stats && <SeasonStatStrip stats={stats} position={position} />}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-nfl-border overflow-x-auto">
        {TABS.map((tab, i) => (
          <button key={tab} onClick={() => setActiveTab(i)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap ${i === activeTab ? 'tab-active' : 'tab-inactive'}`}>
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 0 && <StatsTab stats={stats} gameLog={gameLog} position={position} />}
      {activeTab === 1 && <TrendsTab trends={trends} position={position} />}
      {activeTab === 2 && <SplitsTab splits={splits} />}
      {activeTab === 3 && <ProjectionsTab projection={projection} player={player} />}
    </div>
  );
}

function SeasonStatStrip({ stats, position }: any) {
  const items = position === 'QB'
    ? [{ label: 'Pass Yds', value: stats.total_pass_yards || 0 }, { label: 'TDs', value: stats.total_pass_tds || 0 }, { label: 'INTs', value: stats.total_ints || 0 }, { label: 'Rating', value: Number(stats.avg_qb_rating || 0).toFixed(1) }]
    : position === 'RB'
    ? [{ label: 'Rush Yds', value: stats.total_rush_yards || 0 }, { label: 'TDs', value: stats.total_rush_tds || 0 }, { label: 'Carries', value: stats.total_carries || 0 }, { label: 'Rec Yds', value: stats.total_rec_yards || 0 }]
    : [{ label: 'Rec Yds', value: stats.total_rec_yards || 0 }, { label: 'TDs', value: stats.total_rec_tds || 0 }, { label: 'Rec', value: stats.total_receptions || 0 }, { label: 'Targets', value: stats.total_targets || 0 }];
  return (
    <div className="flex gap-4">
      {items.map(({ label, value }) => (
        <div key={label} className="text-center">
          <div className="text-xl font-bold">{value}</div>
          <div className="text-xs text-gray-400">{label}</div>
        </div>
      ))}
    </div>
  );
}

function StatsTab({ stats, gameLog, position }: any) {
  const statKey = position === 'QB' ? 'qb_yards' : position === 'RB' ? 'rb_yards' : 'rec_yards';
  return (
    <div className="space-y-4">
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {position === 'QB' && <>
            <QuickStat label="Pass Yards" value={stats.total_pass_yards} />
            <QuickStat label="TDs" value={stats.total_pass_tds} />
            <QuickStat label="INTs" value={stats.total_ints} />
            <QuickStat label="QB Rating" value={Number(stats.avg_qb_rating || 0).toFixed(1)} />
          </>}
          {position === 'RB' && <>
            <QuickStat label="Rush Yards" value={stats.total_rush_yards} />
            <QuickStat label="Rush TDs" value={stats.total_rush_tds} />
            <QuickStat label="Carries" value={stats.total_carries} />
            <QuickStat label="Rec Yards" value={stats.total_rec_yards} />
          </>}
          {['WR', 'TE'].includes(position) && <>
            <QuickStat label="Rec Yards" value={stats.total_rec_yards} />
            <QuickStat label="Receptions" value={stats.total_receptions} />
            <QuickStat label="Targets" value={stats.total_targets} />
            <QuickStat label="TDs" value={stats.total_rec_tds} />
          </>}
          <QuickStat label="Fantasy Pts" value={Number(stats.total_fantasy_pts || 0).toFixed(1)} color="text-nfl-gold" />
          <QuickStat label="Games" value={stats.games_played} />
        </div>
      )}
      <div className="card overflow-x-auto">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-400">Game Log</h3>
          {gameLog.length > 0 && (
            <button onClick={() => downloadCSV(
              gameLog.map((g: any) => ({
                Week: g.week, Opp: g.opponent_abbr || '',
                PassYds: g.qb_yards ?? '', RushYds: g.rb_yards ?? '', RecYds: g.rec_yards ?? '',
                TDs: g.qb_touchdowns ?? g.rb_touchdowns ?? g.rec_touchdowns ?? 0,
                Fantasy: Number(g.qb_fantasy_points || g.rb_fantasy_points || g.rec_fantasy_points || 0).toFixed(1),
              })),
              `${player?.full_name?.replace(/\s+/g, '-') || 'player'}-gamelog`
            )} className="btn-ghost text-xs">↓ CSV</button>
          )}
        </div>
        {gameLog.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-nfl-border text-left text-xs text-gray-400">
                <th className="pb-2 pr-4">Wk</th>
                <th className="pb-2 pr-4">Opp</th>
                <th className="pb-2 pr-4">{statKey === 'qb_yards' ? 'Pass Yds' : statKey === 'rb_yards' ? 'Rush Yds' : 'Rec Yds'}</th>
                <th className="pb-2 pr-4">TDs</th>
                <th className="pb-2 pr-4">Fantasy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nfl-border/30">
              {gameLog.map((g: any, i: number) => (
                <tr key={i} className="hover:bg-gray-800/20">
                  <td className="py-2 pr-4 text-gray-400">{g.week}</td>
                  <td className="py-2 pr-4">{g.opponent_abbr || '—'}</td>
                  <td className="py-2 pr-4 font-medium">{g[statKey] ?? '—'}</td>
                  <td className="py-2 pr-4">{position === 'QB' ? g.qb_touchdowns ?? '—' : position === 'RB' ? g.rb_touchdowns ?? '—' : g.rec_touchdowns ?? '—'}</td>
                  <td className="py-2 text-nfl-gold font-medium">
                    {Number((g.qb_fantasy_points || g.rb_fantasy_points || g.rec_fantasy_points || 0)).toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="text-gray-500 text-sm">No game log available yet.</p>}
      </div>
    </div>
  );
}

function TrendsTab({ trends, position }: any) {
  const statKey = position === 'QB' ? 'qb_yards' : position === 'RB' ? 'rb_yards' : 'rec_yards';
  return (
    <div className="space-y-4">
      {trends.length > 0 ? (
        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-3">
            {statKey === 'qb_yards' ? 'Passing' : statKey === 'rb_yards' ? 'Rushing' : 'Receiving'} Yards by Week
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
              <XAxis dataKey="week" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey={statKey} stroke="#013369" strokeWidth={2} dot={{ r: 3 }} name="Actual" />
              <Line type="monotone" dataKey="rolling_3_yards" stroke="#FFB612" strokeWidth={2} strokeDasharray="4 2" dot={false} name="3-Wk Avg" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : <div className="card text-center text-gray-500">Trend data available after 3+ games.</div>}
    </div>
  );
}

function SplitsTab({ splits }: any) {
  if (!splits) return <div className="card text-center text-gray-500">Splits data not yet available.</div>;
  return (
    <div className="card divide-y divide-nfl-border">
      <div className="flex justify-between py-3">
        <span className="text-gray-400">Home Avg Yards</span>
        <span className="font-semibold">{Number(splits.home_yards || 0).toFixed(1)}</span>
      </div>
      <div className="flex justify-between py-3">
        <span className="text-gray-400">Away Avg Yards</span>
        <span className="font-semibold">{Number(splits.away_yards || 0).toFixed(1)}</span>
      </div>
    </div>
  );
}

function ProjectionsTab({ projection, player }: any) {
  if (!projection) return (
    <div className="card text-center text-gray-500 py-8">
      <p>No upcoming game projection available.</p>
      <p className="text-xs mt-1">Projections generate on Wednesdays for that week's games.</p>
    </div>
  );
  const stats = projection.predicted_stats || {};
  const floor = projection.floor_stats || {};
  const ceiling = projection.ceiling_stats || {};
  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Next Game Projection</h3>
          <MatchupRatingBadge rating={projection.matchup_rating || 50} />
        </div>
        <div className="space-y-3">
          {Object.entries(stats).map(([key, val]) => (
            <div key={key} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                <span className="font-semibold">{String(val)}</span>
              </div>
              <div className="relative h-2 bg-gray-700 rounded-full">
                <div className="absolute inset-y-0 left-0 bg-nfl-blue/40 rounded-full"
                  style={{ width: `${Math.min(100, (Number(floor[key]) / Math.max(Number(ceiling[key]), 1)) * 100)}%` }} />
                <div className="absolute inset-y-0 bg-nfl-blue rounded-full"
                  style={{ left: `${Math.min(90, (Number(floor[key]) / Math.max(Number(ceiling[key]), 1)) * 100)}%`, width: 4 }} />
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>Floor: {floor[key]}</span>
                <span>Ceiling: {ceiling[key]}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t border-nfl-border">
          <div className="flex justify-between">
            <span className="text-gray-400 text-sm">Projected PPR</span>
            <span className="font-bold text-nfl-gold text-lg">{projection.projected_fantasy_ppr?.toFixed(1) || '—'} pts</span>
          </div>
        </div>
        {projection.key_factors?.length > 0 && (
          <ul className="mt-3 space-y-1 text-xs text-gray-400">
            {projection.key_factors.map((f: string, i: number) => <li key={i}>• {f}</li>)}
          </ul>
        )}
      </div>
    </div>
  );
}

function QuickStat({ label, value, color = 'text-white' }: any) {
  return (
    <div className="card text-center">
      <div className={`text-xl font-bold ${color}`}>{value ?? '—'}</div>
      <div className="text-xs text-gray-400 mt-1">{label}</div>
    </div>
  );
}
