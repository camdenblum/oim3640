import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { endpoints } from '../utils/api';
import InjuryStatusBadge from '../components/InjuryStatusBadge';
import { TableSkeleton } from '../components/LoadingSkeleton';
import { downloadCSV } from '../utils/csv';

const POSITIONS = ['All', 'QB', 'RB', 'WR', 'TE', 'OL', 'DL', 'LB', 'CB', 'S', 'K'];
const STAT_LEADERS = [
  { label: 'Pass Yards', stat: 'qb_yards', pos: 'QB' },
  { label: 'Rush Yards', stat: 'rb_yards', pos: 'RB' },
  { label: 'Rec Yards', stat: 'rec_yards', pos: 'WR' },
  { label: 'Receptions', stat: 'receptions', pos: 'WR' },
  { label: 'Pass TDs', stat: 'qb_tds', pos: 'QB' },
  { label: 'Sacks', stat: 'sacks', pos: 'LB' },
];

export default function PlayersPage() {
  const [position, setPosition] = useState('All');
  const [search, setSearch] = useState('');
  const [activeLeader, setActiveLeader] = useState(0);
  const [page, setPage] = useState(1);

  const { data: playersRes, isLoading } = useQuery({
    queryKey: ['players', position, page],
    queryFn: () => endpoints.players.all({ position: position === 'All' ? undefined : position, page, limit: 50 }),
  });

  const { data: searchRes } = useQuery({
    queryKey: ['player-search', search],
    queryFn: () => endpoints.players.search(search),
    enabled: search.length >= 2,
  });

  const { data: leaderRes } = useQuery({
    queryKey: ['leaderboard', STAT_LEADERS[activeLeader].stat, STAT_LEADERS[activeLeader].pos],
    queryFn: () => endpoints.players.leaderboards({
      stat: STAT_LEADERS[activeLeader].stat,
      position: STAT_LEADERS[activeLeader].pos,
    }),
  });

  const players: any[] = search.length >= 2 ? (searchRes?.data || []) : (playersRes?.data || []);
  const leaders: any[] = leaderRes?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">Players</h1>
        <div className="flex items-center gap-2">
          {players.length > 0 && (
            <button
              onClick={() => downloadCSV(
                players.map((p: any) => ({
                  Name: p.full_name, Position: p.position, Team: p.team_abbr || 'FA',
                  Jersey: p.jersey_number || '', Status: p.injury_status || 'Active',
                  Experience: p.years_experience != null ? `${p.years_experience}yr` : '',
                  College: p.college || '',
                })),
                `nfl-players-${position.toLowerCase()}`
              )}
              className="btn-ghost text-xs flex items-center gap-1">
              ↓ CSV
            </button>
          )}
          <div className="relative">
          <input
            type="text" placeholder="Search players…" value={search}
            onChange={e => setSearch(e.target.value)}
            data-shortcut-search
            className="bg-gray-800 border border-nfl-border rounded-lg px-4 py-2 text-sm w-56 focus:outline-none focus:border-nfl-blue" />
            {search && (
              <button onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white">✕</button>
            )}
          </div>
        </div>
      </div>

      {/* Leaderboards */}
      <div className="card">
        <div className="flex gap-2 flex-wrap mb-4">
          {STAT_LEADERS.map((l, i) => (
            <button key={i} onClick={() => setActiveLeader(i)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${i === activeLeader ? 'bg-nfl-gold text-black' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}>
              {l.label}
            </button>
          ))}
        </div>
        {leaders.length > 0 ? (
          <div className="divide-y divide-nfl-border">
            {leaders.slice(0, 10).map((p: any, i: number) => (
              <div key={p.id} className="flex items-center gap-3 py-2">
                <span className="w-6 text-xs text-gray-500 font-mono">{i + 1}</span>
                <Link to={`/players/${p.id}`} className="flex-1 font-medium text-sm hover:text-nfl-gold">{p.full_name}</Link>
                <span className="text-xs text-gray-400">{p.team_abbr}</span>
                <span className="font-bold text-nfl-gold text-sm">{Number(p.stat_value || 0).toFixed(0)}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm text-center py-4">Leaderboards populate as game data syncs.</p>
        )}
      </div>

      {/* Position Filter */}
      <div className="flex gap-1 flex-wrap">
        {POSITIONS.map(pos => (
          <button key={pos} onClick={() => { setPosition(pos); setPage(1); }}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${position === pos ? 'bg-nfl-blue text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}>
            {pos}
          </button>
        ))}
      </div>

      {/* Players Table */}
      <div className="card overflow-x-auto">
        {isLoading ? <TableSkeleton rows={10} /> : players.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-nfl-border text-left text-xs text-gray-400">
                <th className="pb-2 pr-4">Player</th>
                <th className="pb-2 pr-4">Pos</th>
                <th className="pb-2 pr-4">Team</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Exp</th>
                <th className="pb-2">College</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nfl-border/30">
              {players.map((p: any) => (
                <tr key={p.id} className="hover:bg-gray-800/20">
                  <td className="py-2.5 pr-4">
                    <Link to={`/players/${p.id}`} className="font-medium hover:text-nfl-gold">{p.full_name}</Link>
                    {p.jersey_number && <span className="text-xs text-gray-500 ml-1">#{p.jersey_number}</span>}
                  </td>
                  <td className="py-2.5 pr-4">
                    <span className="badge bg-gray-700 text-gray-200">{p.position}</span>
                  </td>
                  <td className="py-2.5 pr-4">
                    {p.team_id ? (
                      <Link to={`/teams/${p.team_id}`} className="text-gray-400 hover:text-nfl-gold text-xs font-medium">
                        {p.team_abbr || '—'}
                      </Link>
                    ) : <span className="text-gray-500">FA</span>}
                  </td>
                  <td className="py-2.5 pr-4"><InjuryStatusBadge status={p.injury_status} /></td>
                  <td className="py-2.5 pr-4 text-gray-400 text-xs">{p.years_experience != null ? `${p.years_experience}yr` : '—'}</td>
                  <td className="py-2.5 text-gray-400 text-xs truncate max-w-[120px]">{p.college || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center text-gray-500 py-12">
            <p>No players found{position !== 'All' ? ` at ${position}` : ''}.</p>
            <p className="text-xs mt-1">Player data syncs automatically from ESPN.</p>
          </div>
        )}
        {!search && players.length >= 50 && (
          <div className="flex justify-between items-center mt-4 pt-4 border-t border-nfl-border">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
              className="btn-ghost disabled:opacity-30 text-sm">← Prev</button>
            <span className="text-xs text-gray-400">Page {page}</span>
            <button onClick={() => setPage(p => p + 1)} className="btn-ghost text-sm">Next →</button>
          </div>
        )}
      </div>
    </div>
  );
}
