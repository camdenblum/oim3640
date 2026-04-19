import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { endpoints } from '../utils/api';
import StatCard from '../components/StatCard';
import InjuryStatusBadge from '../components/InjuryStatusBadge';
import { CardSkeleton, Skeleton } from '../components/LoadingSkeleton';
import { formatRecord, formatStat, computeWinPct } from '../utils/stats';

const TABS = ['Overview', 'Offense', 'Defense', 'Advanced', 'Schedule', 'Roster'];

export default function TeamDetailPage() {
  const { id } = useParams<{ id: string }>();
  const teamId = Number(id);
  const [activeTab, setActiveTab] = useState(0);

  const { data: teamRes, isLoading } = useQuery({ queryKey: ['team', teamId], queryFn: () => endpoints.teams.byId(teamId) });
  const { data: statsRes } = useQuery({ queryKey: ['team-stats', teamId], queryFn: () => endpoints.teams.stats(teamId) });
  const { data: weeklyRes } = useQuery({ queryKey: ['team-weekly', teamId], queryFn: () => endpoints.teams.weeklyStats(teamId) });
  const { data: scheduleRes } = useQuery({ queryKey: ['team-schedule', teamId], queryFn: () => endpoints.teams.schedule(teamId) });
  const { data: rosterRes } = useQuery({ queryKey: ['team-roster', teamId], queryFn: () => endpoints.teams.roster(teamId), enabled: activeTab === 5 });
  const { data: injuryRes } = useQuery({ queryKey: ['team-injuries', teamId], queryFn: () => endpoints.teams.injuries(teamId) });
  const { data: advancedRes } = useQuery({ queryKey: ['team-advanced', teamId], queryFn: () => endpoints.teams.advanced(teamId), enabled: activeTab === 3 });

  const team = teamRes?.data;
  const stats = statsRes?.data;
  const weekly: any[] = weeklyRes?.data || [];
  const schedule: any[] = scheduleRes?.data || [];
  const roster: any[] = rosterRes?.data || [];
  const injuries: any[] = injuryRes?.data || [];
  const advanced = advancedRes?.data;

  if (isLoading) return <div className="space-y-4"><Skeleton className="h-32 w-full" /><CardSkeleton /></div>;
  if (!team) return <div className="card text-center text-gray-500">Team not found</div>;

  const finishedGames = schedule.filter(g => g.status === 'final');
  const wins = finishedGames.filter(g => (g.home_team_id === teamId ? g.home_score > g.away_score : g.away_score > g.home_score)).length;
  const losses = finishedGames.length - wins;

  return (
    <div className="space-y-6">
      {/* Team Header */}
      <div className="card" style={{ borderTopColor: team.primary_color, borderTopWidth: 3 }}>
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full flex items-center justify-center text-xl font-black text-white"
            style={{ backgroundColor: team.primary_color }}>
            {team.abbreviation}
          </div>
          <div>
            <h1 className="text-2xl font-bold">{team.city} {team.name}</h1>
            <div className="flex gap-3 text-sm text-gray-400 mt-1">
              <span>{team.conference} · {team.division}</span>
              <span className="font-bold text-white">{formatRecord(wins, losses)}</span>
              {stats && <span>PPG: {Number(stats.ppg || 0).toFixed(1)}</span>}
              {stats && <span>Allowed: {Number(stats.ppg_allowed || 0).toFixed(1)}</span>}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-nfl-border overflow-x-auto">
        {TABS.map((tab, i) => (
          <button key={tab} onClick={() => setActiveTab(i)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors ${i === activeTab ? 'tab-active' : 'tab-inactive'}`}>
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 0 && <OverviewTab stats={stats} weekly={weekly} injuries={injuries} teamId={teamId} finishedGames={finishedGames} wins={wins} losses={losses} />}
      {activeTab === 1 && <OffenseTab stats={stats} />}
      {activeTab === 2 && <DefenseTab stats={stats} />}
      {activeTab === 3 && <AdvancedTab advanced={advanced} />}
      {activeTab === 4 && <ScheduleTab schedule={schedule} teamId={teamId} />}
      {activeTab === 5 && <RosterTab roster={roster} injuries={injuries} />}
    </div>
  );
}

function OverviewTab({ stats, weekly, injuries, teamId, finishedGames, wins, losses }: any) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard label="PPG" value={Number(stats?.ppg || 0).toFixed(1)} color="text-green-400" />
        <StatCard label="PPG Allowed" value={Number(stats?.ppg_allowed || 0).toFixed(1)} color="text-red-400" />
        <StatCard label="Yds/Game" value={Number(stats?.yards_per_game || 0).toFixed(0)} />
        <StatCard label="Pass Yds/G" value={Number(stats?.pass_yards_per_game || 0).toFixed(0)} />
        <StatCard label="Rush Yds/G" value={Number(stats?.rush_yards_per_game || 0).toFixed(0)} />
        <StatCard label="3rd Down%" value={`${(Number(stats?.third_down_pct || 0) * 100).toFixed(1)}%`} />
      </div>

      {/* Weekly scoring trend */}
      {weekly.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Points Scored by Week</h3>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={weekly}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
              <XAxis dataKey="week" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey="points_scored" stroke="#013369" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="points_allowed" stroke="#D50A0A" strokeWidth={2} dot={{ r: 3 }} strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Last 5 games */}
      {finishedGames.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Recent Games</h3>
          <div className="flex gap-2 flex-wrap">
            {finishedGames.slice(-5).reverse().map((g: any) => {
              const isHome = g.home_team_id === teamId;
              const teamScore = isHome ? g.home_score : g.away_score;
              const oppScore = isHome ? g.away_score : g.home_score;
              const won = teamScore > oppScore;
              const oppAbbr = isHome ? g.away_abbr : g.home_abbr;
              return (
                <Link key={g.id} to={`/games/${g.id}`}
                  className={`flex flex-col items-center p-3 rounded-lg border min-w-[80px] ${won ? 'border-green-700/50 bg-green-900/20' : 'border-red-700/50 bg-red-900/20'}`}>
                  <span className={`font-bold ${won ? 'text-green-400' : 'text-red-400'}`}>{won ? 'W' : 'L'}</span>
                  <span className="text-sm font-medium">{teamScore}–{oppScore}</span>
                  <span className="text-xs text-gray-500">{isHome ? 'vs' : '@'} {oppAbbr}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Injuries */}
      {injuries.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Injury Report</h3>
          <div className="divide-y divide-nfl-border">
            {injuries.slice(0, 8).map((p: any) => (
              <div key={p.id} className="flex items-center justify-between py-2">
                <Link to={`/players/${p.id}`} className="text-sm hover:text-nfl-gold">{p.full_name}</Link>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <span>{p.position}</span>
                  <InjuryStatusBadge status={p.injury_status} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function OffenseTab({ stats }: any) {
  if (!stats) return <div className="card text-center text-gray-500">No offensive stats available yet.</div>;
  const rows = [
    { label: 'Points Per Game', value: Number(stats.ppg || 0).toFixed(1) },
    { label: 'Total Yards/Game', value: Number(stats.yards_per_game || 0).toFixed(0) },
    { label: 'Passing Yards/Game', value: Number(stats.pass_yards_per_game || 0).toFixed(0) },
    { label: 'Rushing Yards/Game', value: Number(stats.rush_yards_per_game || 0).toFixed(0) },
    { label: 'Completion %', value: `${Number(stats.completion_pct || 0).toFixed(1)}%` },
    { label: '3rd Down %', value: `${(Number(stats.third_down_pct || 0) * 100).toFixed(1)}%` },
    { label: 'Red Zone TD %', value: `${(Number(stats.rz_td_pct || 0) * 100).toFixed(1)}%` },
    { label: 'Yards Per Play', value: Number(stats.yards_per_play || 0).toFixed(2) },
    { label: 'Turnovers', value: Number(stats.total_turnovers || 0).toFixed(1) },
  ];
  return <StatsTable rows={rows} />;
}

function DefenseTab({ stats }: any) {
  if (!stats) return <div className="card text-center text-gray-500">No defensive stats available yet.</div>;
  const rows = [
    { label: 'Points Allowed/Game', value: Number(stats.ppg_allowed || 0).toFixed(1) },
    { label: 'Sacks/Game', value: Number(stats.sacks_per_game || 0).toFixed(1) },
    { label: 'Interceptions', value: Number(stats.interceptions || 0).toFixed(0) },
    { label: 'EPA Per Play Allowed', value: Number(stats.epa_per_play || 0).toFixed(3) },
  ];
  return <StatsTable rows={rows} />;
}

function AdvancedTab({ advanced }: any) {
  if (!advanced) return <div className="card text-center text-gray-500">Advanced metrics load after 4+ games.</div>;
  const rows = [
    { label: 'EPA Per Play', value: Number(advanced.avg_epa_per_play || 0).toFixed(3) },
    { label: 'Success Rate', value: `${(Number(advanced.avg_success_rate || 0) * 100).toFixed(1)}%` },
    { label: 'Blitz Rate', value: `${(Number(advanced.avg_blitz_rate || 0) * 100).toFixed(1)}%` },
    { label: 'Pressure Rate', value: `${(Number(advanced.avg_pressure_rate || 0) * 100).toFixed(1)}%` },
    { label: 'Elo Rating', value: Number(advanced.elo_rating || 1500).toFixed(0) },
  ];
  return <StatsTable rows={rows} />;
}

function ScheduleTab({ schedule, teamId }: any) {
  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-nfl-border text-left text-xs text-gray-400">
            <th className="pb-2 pr-4">Wk</th>
            <th className="pb-2 pr-4">Opponent</th>
            <th className="pb-2 pr-4">H/A</th>
            <th className="pb-2 pr-4">Result</th>
            <th className="pb-2">Date</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-nfl-border/30">
          {schedule.map((g: any) => {
            const isHome = g.home_team_id === teamId;
            const teamScore = isHome ? g.home_score : g.away_score;
            const oppScore = isHome ? g.away_score : g.home_score;
            const oppAbbr = isHome ? g.away_abbr : g.home_abbr;
            const isFinal = g.status === 'final';
            const won = isFinal && teamScore > oppScore;
            return (
              <tr key={g.id} className="hover:bg-gray-800/20">
                <td className="py-2 pr-4 text-gray-400">{g.week}</td>
                <td className="py-2 pr-4">
                  <Link to={`/teams/${isHome ? g.away_team_id : g.home_team_id}`} className="hover:text-nfl-gold">{oppAbbr}</Link>
                </td>
                <td className="py-2 pr-4 text-gray-400">{isHome ? 'H' : 'A'}</td>
                <td className="py-2 pr-4">
                  {isFinal ? (
                    <span className={won ? 'text-green-400 font-bold' : 'text-red-400 font-bold'}>
                      {won ? 'W' : 'L'} {teamScore}–{oppScore}
                    </span>
                  ) : g.status === 'in_progress' ? (
                    <span className="text-yellow-400">LIVE</span>
                  ) : (
                    <span className="text-gray-500">—</span>
                  )}
                </td>
                <td className="py-2 text-xs text-gray-400">{new Date(g.game_date).toLocaleDateString()}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RosterTab({ roster, injuries }: any) {
  const injuryMap = Object.fromEntries(injuries.map((p: any) => [p.id, p.injury_status]));
  const byPosition = roster.reduce((acc: any, p: any) => {
    if (!acc[p.position]) acc[p.position] = [];
    acc[p.position].push(p);
    return acc;
  }, {});
  const positions = ['QB', 'RB', 'WR', 'TE', 'OL', 'DL', 'LB', 'CB', 'S', 'K', 'P'];
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {positions.filter(pos => byPosition[pos]?.length).map(pos => (
        <div key={pos} className="card">
          <h3 className="text-sm font-semibold text-nfl-gold mb-2">{pos}</h3>
          <div className="space-y-1">
            {byPosition[pos].map((p: any) => (
              <div key={p.id} className="flex items-center justify-between py-1">
                <div className="flex items-center gap-2">
                  {p.is_starter && <span className="w-1.5 h-1.5 rounded-full bg-nfl-gold" />}
                  <Link to={`/players/${p.id}`} className="text-sm hover:text-nfl-gold">{p.full_name}</Link>
                </div>
                <InjuryStatusBadge status={injuryMap[p.id] || p.injury_status} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function StatsTable({ rows }: { rows: { label: string; value: string }[] }) {
  return (
    <div className="card divide-y divide-nfl-border">
      {rows.map(({ label, value }) => (
        <div key={label} className="flex items-center justify-between py-3">
          <span className="text-sm text-gray-400">{label}</span>
          <span className="font-semibold">{value}</span>
        </div>
      ))}
    </div>
  );
}
