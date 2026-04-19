import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { endpoints } from '../utils/api';
import { Skeleton } from '../components/LoadingSkeleton';
import { downloadCSV } from '../utils/csv';

export default function PowerRankingsPage() {
  const { currentWeek, currentSeason } = useAppStore();

  const { data: res, isLoading } = useQuery({
    queryKey: ['power-rankings', currentWeek, currentSeason],
    queryFn: () => endpoints.analytics.powerRankings(currentWeek, currentSeason),
  });

  const teams: any[] = res?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Power Rankings</h1>
          <p className="text-gray-400 text-sm mt-1">
            Algorithm: Elo (35%) + Recent EPA (30%) + Point Differential (20%) + SOS (15%) · Week {currentWeek}
          </p>
        </div>
        {teams.length > 0 && (
          <button onClick={() => downloadCSV(
            teams.map((t: any, i: number) => ({
              Rank: i + 1, Team: t.abbreviation,
              Elo: Number(t.elo_rating || 1500).toFixed(0),
              Delta: (Number(t.elo_rating || 1500) - 1500).toFixed(0),
              Record: `${t.wins || 0}-${t.losses || 0}`,
            })),
            `nfl-power-rankings-week${currentWeek}-${currentSeason}`
          )} className="btn-ghost text-sm">↓ Export CSV</button>
        )}
      </div>

      <div className="card overflow-x-auto">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 32 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : teams.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-nfl-border text-left text-xs text-gray-400">
                <th className="pb-2 w-10">Rank</th>
                <th className="pb-2 pr-4">Team</th>
                <th className="pb-2 pr-4">Conf</th>
                <th className="pb-2 pr-4">Elo Rating</th>
                <th className="pb-2 pr-4">EPA/Play</th>
                <th className="pb-2 pr-4">Pt Diff</th>
                <th className="pb-2">Trend</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nfl-border/30">
              {teams.map((team: any, i: number) => {
                const eloFromAvg = (team.elo || 1500) - 1500;
                const isElite = i < 4;
                const isBad = i >= 28;
                return (
                  <tr key={team.id}
                    className={`hover:bg-gray-800/20 ${isElite ? 'bg-green-900/10' : isBad ? 'bg-red-900/10' : ''}`}>
                    <td className="py-3 pr-2">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                        isElite ? 'bg-green-900/50 text-green-300' :
                        isBad ? 'bg-red-900/50 text-red-300' : 'bg-gray-800 text-gray-300'}`}>
                        {i + 1}
                      </div>
                    </td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white"
                          style={{ backgroundColor: team.primary_color || '#013369' }}>
                          {team.abbreviation?.slice(0, 2)}
                        </div>
                        <div>
                          <Link to={`/teams/${team.id}`} className="font-semibold hover:text-nfl-gold">{team.name}</Link>
                          <div className="text-xs text-gray-500">{team.abbreviation}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 pr-4">
                      <span className={`badge ${team.conference === 'AFC' ? 'bg-blue-900/40 text-blue-300' : 'bg-red-900/30 text-red-300'}`}>
                        {team.conference}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <div className="font-mono font-semibold">{Math.round(team.elo || 1500)}</div>
                      <div className={`text-xs ${eloFromAvg >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {eloFromAvg > 0 ? '+' : ''}{eloFromAvg.toFixed(0)} vs avg
                      </div>
                    </td>
                    <td className="py-3 pr-4">
                      <span className={Number(team.avg_epa || 0) >= 0 ? 'text-green-400' : 'text-red-400'}>
                        {Number(team.avg_epa || 0) >= 0 ? '+' : ''}{Number(team.avg_epa || 0).toFixed(3)}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <span className={Number(team.avg_point_diff || 0) >= 0 ? 'text-green-400' : 'text-red-400'}>
                        {Number(team.avg_point_diff || 0) >= 0 ? '+' : ''}{Number(team.avg_point_diff || 0).toFixed(1)}
                      </span>
                    </td>
                    <td className="py-3">
                      <div className="w-24 h-1.5 bg-gray-700 rounded-full">
                        <div className="h-1.5 rounded-full bg-nfl-blue"
                          style={{ width: `${Math.max(5, ((team.elo || 1500) - 1200) / 8)}%` }} />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="text-center text-gray-500 py-16">
            <p className="text-lg">Power rankings calculate after team data syncs.</p>
            <p className="text-sm mt-2">Check back once the backend has loaded teams from ESPN.</p>
          </div>
        )}
      </div>

      <div className="card text-xs text-gray-400 space-y-1">
        <p><span className="text-white font-medium">Green rows</span> = Top 4 seeds · <span className="text-white font-medium">Red rows</span> = Bottom 4 teams</p>
        <p>Elo rating resets each season to a blend of prior year rating and 1500 (regression to mean).</p>
        <p>EPA (Expected Points Added) per play measures offensive efficiency adjusted for game situation.</p>
      </div>
    </div>
  );
}
