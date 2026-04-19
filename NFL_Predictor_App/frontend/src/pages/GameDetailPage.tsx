import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { endpoints } from '../utils/api';
import { CardSkeleton } from '../components/LoadingSkeleton';

export default function GameDetailPage() {
  const { id } = useParams<{ id: string }>();
  const gameId = Number(id);

  const { data: gameRes, isLoading } = useQuery({ queryKey: ['game', gameId], queryFn: () => endpoints.games.byId(gameId) });
  const { data: boxRes } = useQuery({ queryKey: ['box-score', gameId], queryFn: () => endpoints.games.boxScore(gameId) });

  const game = gameRes?.data;
  const box = boxRes?.data;

  if (isLoading) return <div className="space-y-4"><CardSkeleton /><CardSkeleton /></div>;
  if (!game) return <div className="card text-center text-gray-500">Game not found</div>;

  const isFinal = game.status === 'final';
  const homeTeamStats = box?.teamStats?.find((t: any) => t.team_id === game.home_team_id);
  const awayTeamStats = box?.teamStats?.find((t: any) => t.team_id === game.away_team_id);

  return (
    <div className="space-y-6">
      {/* Game Header */}
      <div className="card">
        <div className="text-center mb-4">
          <span className={`badge ${isFinal ? 'bg-gray-700 text-gray-300' : 'bg-green-900 text-green-300'}`}>
            {isFinal ? 'FINAL' : game.status?.toUpperCase()}
          </span>
        </div>
        <div className="grid grid-cols-3 items-center gap-4">
          <TeamHeader team={{ abbr: game.away_abbr, name: game.away_team_name, color: game.away_color, id: game.away_team_id }}
            score={game.away_score} side="away" />
          <div className="text-center text-gray-400 text-sm space-y-1">
            <div>{new Date(game.game_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</div>
            <div>{game.venue}</div>
            {game.weather_temp_f && <div className="text-blue-400 text-xs">{game.weather_temp_f}°F · {game.weather_wind_mph}mph wind</div>}
            <div className="text-xs">{game.broadcast_network}</div>
          </div>
          <TeamHeader team={{ abbr: game.home_abbr, name: game.home_team_name, color: game.home_color, id: game.home_team_id }}
            score={game.home_score} side="home" />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3">
        <Link to={`/predict/game/${gameId}`} className="btn-primary text-sm flex-1 text-center">
          View Full Prediction Breakdown →
        </Link>
      </div>

      {/* Team Stats Comparison */}
      {isFinal && homeTeamStats && awayTeamStats && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Team Stats Comparison</h2>
          <div className="space-y-3">
            {[
              { label: 'Total Yards', home: homeTeamStats.total_yards, away: awayTeamStats.total_yards, higher: 'better' },
              { label: 'Passing Yards', home: homeTeamStats.passing_yards, away: awayTeamStats.passing_yards, higher: 'better' },
              { label: 'Rushing Yards', home: homeTeamStats.rushing_yards, away: awayTeamStats.rushing_yards, higher: 'better' },
              { label: 'First Downs', home: homeTeamStats.first_downs, away: awayTeamStats.first_downs, higher: 'better' },
              { label: '3rd Down Conv', home: homeTeamStats.third_down_conversions, away: awayTeamStats.third_down_conversions, higher: 'better' },
              { label: 'Turnovers', home: homeTeamStats.turnovers, away: awayTeamStats.turnovers, higher: 'lower' },
              { label: 'Sacks', home: homeTeamStats.sacks, away: awayTeamStats.sacks, higher: 'better' },
              { label: 'Penalties', home: homeTeamStats.penalties, away: awayTeamStats.penalties, higher: 'lower' },
            ].map(stat => <StatBar key={stat.label} {...stat} homeAbbr={game.home_abbr} awayAbbr={game.away_abbr} />)}
          </div>
        </div>
      )}

      {/* Box Score Players */}
      {box?.playerStats?.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Player Box Score</h2>
          {(['QB', 'RB', 'WR', 'TE'] as const).map(pos => {
            const posPlayers = box.playerStats.filter((p: any) => p.position === pos);
            if (!posPlayers.length) return null;
            return (
              <div key={pos} className="mb-4">
                <h3 className="text-xs font-semibold text-nfl-gold uppercase tracking-wider mb-2">{pos}</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-nfl-border text-left text-gray-500">
                        <th className="pb-1 pr-3">Player</th>
                        <th className="pb-1 pr-3">Team</th>
                        {pos === 'QB' && <><th className="pb-1 pr-3">Comp/Att</th><th className="pb-1 pr-3">Yards</th><th className="pb-1 pr-3">TD</th><th className="pb-1">INT</th></>}
                        {pos === 'RB' && <><th className="pb-1 pr-3">Car</th><th className="pb-1 pr-3">Yds</th><th className="pb-1 pr-3">TD</th><th className="pb-1">Rec Yds</th></>}
                        {(pos === 'WR' || pos === 'TE') && <><th className="pb-1 pr-3">Tar</th><th className="pb-1 pr-3">Rec</th><th className="pb-1 pr-3">Yds</th><th className="pb-1">TD</th></>}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-nfl-border/20">
                      {posPlayers.map((p: any) => (
                        <tr key={p.player_id} className="hover:bg-gray-800/20">
                          <td className="py-1.5 pr-3"><Link to={`/players/${p.player_id}`} className="hover:text-nfl-gold">{p.full_name}</Link></td>
                          <td className="py-1.5 pr-3 text-gray-400">{p.team_abbr}</td>
                          {pos === 'QB' && <><td className="pr-3">{p.qb_completions ?? 0}/{p.qb_attempts ?? 0}</td><td className="pr-3">{p.qb_yards ?? 0}</td><td className="pr-3">{p.qb_touchdowns ?? 0}</td><td>{p.qb_interceptions ?? 0}</td></>}
                          {pos === 'RB' && <><td className="pr-3">{p.rb_carries ?? 0}</td><td className="pr-3">{p.rb_yards ?? 0}</td><td className="pr-3">{p.rb_touchdowns ?? 0}</td><td>{p.rb_receiving_yards ?? 0}</td></>}
                          {(pos === 'WR' || pos === 'TE') && <><td className="pr-3">{p.rec_targets ?? 0}</td><td className="pr-3">{p.rec_receptions ?? 0}</td><td className="pr-3">{p.rec_yards ?? 0}</td><td>{p.rec_touchdowns ?? 0}</td></>}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function TeamHeader({ team, score, side }: any) {
  return (
    <Link to={`/teams/${team.id}`}
      className={`flex flex-col items-center gap-2 hover:opacity-80 transition-opacity ${side === 'home' ? 'items-end' : 'items-start'}`}>
      <div className="w-14 h-14 rounded-full flex items-center justify-center font-black text-white text-sm"
        style={{ backgroundColor: team.color || '#1a1a2e' }}>
        {team.abbr}
      </div>
      <div className={`font-semibold ${side === 'home' ? 'text-right' : 'text-left'}`}>{team.name}</div>
      {score != null && <div className="text-4xl font-black">{score}</div>}
    </Link>
  );
}

function StatBar({ label, home, away, higher, homeAbbr, awayAbbr }: any) {
  const total = (Number(home) || 0) + (Number(away) || 0);
  const homePct = total > 0 ? (Number(home) / total) * 100 : 50;
  const homeBetter = higher === 'better' ? home >= away : home <= away;
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className={`font-semibold ${homeBetter ? 'text-green-400' : 'text-white'}`}>{home ?? 0}</span>
        <span className="text-gray-400">{label}</span>
        <span className={`font-semibold ${!homeBetter ? 'text-green-400' : 'text-white'}`}>{away ?? 0}</span>
      </div>
      <div className="flex h-2 rounded-full overflow-hidden bg-gray-700">
        <div className="bg-nfl-blue transition-all" style={{ width: `${homePct}%` }} />
        <div className="bg-nfl-red flex-1 transition-all" />
      </div>
    </div>
  );
}
