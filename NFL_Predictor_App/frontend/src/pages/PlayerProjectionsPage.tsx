import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { endpoints } from '../utils/api';
import MatchupRatingBadge from '../components/MatchupRatingBadge';
import { TableSkeleton } from '../components/LoadingSkeleton';

const POSITIONS = ['All', 'QB', 'RB', 'WR', 'TE'];

export default function PlayerProjectionsPage() {
  const { currentWeek } = useAppStore();
  const [position, setPosition] = useState('All');
  const [sortBy, setSortBy] = useState<'ppr' | 'std' | 'matchup'>('ppr');

  const { data: leaderboardRes, isLoading } = useQuery({
    queryKey: ['leaderboard', position, currentWeek],
    queryFn: () => endpoints.players.leaderboards({
      position: position === 'All' ? 'QB' : position,
      week: currentWeek,
    }),
  });

  const players: any[] = (leaderboardRes?.data || [])
    .sort((a: any, b: any) => {
      if (sortBy === 'matchup') return (b.matchup_rating || 50) - (a.matchup_rating || 50);
      return (b.projected_fantasy_ppr || 0) - (a.projected_fantasy_ppr || 0);
    });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Player Projections</h1>
          <p className="text-gray-400 text-sm">Week {currentWeek} fantasy & performance projections</p>
        </div>
        <Link to="/predict" className="text-sm text-gray-400 hover:text-white">← Game Predictions</Link>
      </div>

      <div className="flex gap-3 flex-wrap items-center">
        <div className="flex gap-1 rounded-lg border border-nfl-border overflow-hidden">
          {POSITIONS.map(pos => (
            <button key={pos} onClick={() => setPosition(pos)}
              className={`px-3 py-1.5 text-xs font-medium transition-colors ${position === pos ? 'bg-nfl-blue text-white' : 'text-gray-400 hover:bg-gray-800'}`}>
              {pos}
            </button>
          ))}
        </div>
        <div className="flex gap-1 rounded-lg border border-nfl-border overflow-hidden ml-auto">
          {[['ppr', 'PPR Pts'], ['std', 'Std Pts'], ['matchup', 'Matchup']].map(([v, label]) => (
            <button key={v} onClick={() => setSortBy(v as any)}
              className={`px-3 py-1.5 text-xs font-medium transition-colors ${sortBy === v ? 'bg-nfl-gold text-black' : 'text-gray-400 hover:bg-gray-800'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="card overflow-x-auto">
        {isLoading ? <TableSkeleton rows={15} /> : players.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-nfl-border text-left text-xs text-gray-400">
                <th className="pb-2 pr-3 w-6">#</th>
                <th className="pb-2 pr-4">Player</th>
                <th className="pb-2 pr-4">Pos</th>
                <th className="pb-2 pr-4">Team</th>
                <th className="pb-2 pr-4">Matchup</th>
                <th className="pb-2 pr-4">Proj PPR</th>
                <th className="pb-2 pr-4">Proj Std</th>
                <th className="pb-2">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nfl-border/30">
              {players.map((p: any, i: number) => (
                <tr key={p.id || i} className="hover:bg-gray-800/20">
                  <td className="py-2.5 pr-3 text-gray-500 text-xs font-mono">{i + 1}</td>
                  <td className="py-2.5 pr-4">
                    <Link to={`/players/${p.id}`} className="font-medium hover:text-nfl-gold">{p.full_name}</Link>
                  </td>
                  <td className="py-2.5 pr-4"><span className="badge bg-gray-700 text-gray-200">{p.position}</span></td>
                  <td className="py-2.5 pr-4 text-gray-400 text-xs">{p.team_abbr}</td>
                  <td className="py-2.5 pr-4"><MatchupRatingBadge rating={p.matchup_rating || 50} /></td>
                  <td className="py-2.5 pr-4 font-bold text-nfl-gold">{p.projected_fantasy_ppr?.toFixed(1) || '—'}</td>
                  <td className="py-2.5 pr-4 text-gray-300">{p.projected_fantasy_std?.toFixed(1) || '—'}</td>
                  <td className="py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-gray-700 rounded-full">
                        <div className="h-1.5 rounded-full bg-nfl-blue" style={{ width: `${(p.confidence_score || 0.5) * 100}%` }} />
                      </div>
                      <span className="text-xs text-gray-500">{((p.confidence_score || 0.5) * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center text-gray-500 py-12">
            <p>Player projections for Week {currentWeek} are not yet available.</p>
            <p className="text-xs mt-1">Projections are generated on Wednesdays after the model ingests the latest data.</p>
          </div>
        )}
      </div>
    </div>
  );
}
