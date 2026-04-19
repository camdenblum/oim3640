import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { endpoints } from '../utils/api';
import { GameCardSkeleton } from '../components/LoadingSkeleton';

export default function GamesPage() {
  const { currentWeek, currentSeason, setWeek } = useAppStore();
  const [filter, setFilter] = useState<'all' | 'final' | 'scheduled' | 'in_progress'>('all');

  const { data: gamesRes, isLoading } = useQuery({
    queryKey: ['games', currentSeason, currentWeek],
    queryFn: () => endpoints.games.all({ season: currentSeason, week: currentWeek }),
    refetchInterval: filter === 'in_progress' ? 30000 : false,
  });

  const { data: liveRes } = useQuery({
    queryKey: ['live-games'],
    queryFn: () => endpoints.games.live(),
    refetchInterval: 30000,
  });

  const allGames: any[] = gamesRes?.data || [];
  const liveGames: any[] = liveRes?.data || [];
  const games = filter === 'all' ? allGames : allGames.filter(g => g.status === filter);

  return (
    <div className="space-y-6">
      {/* Live Games Banner */}
      {liveGames.length > 0 && (
        <div className="bg-green-900/30 border border-green-700/50 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-green-400 font-semibold text-sm">LIVE NOW</span>
          </div>
          <div className="flex gap-3 overflow-x-auto pb-1">
            {liveGames.map((g: any) => (
              <Link key={g.id} to={`/games/${g.id}`}
                className="flex-shrink-0 bg-gray-800 rounded-lg px-4 py-2 text-sm hover:bg-gray-700 transition-colors">
                <span className="font-bold">{g.away_abbr} {g.away_score}</span>
                <span className="text-gray-400 mx-2">—</span>
                <span className="font-bold">{g.home_score} {g.home_abbr}</span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Header & Controls */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">Games</h1>
          <p className="text-sm text-gray-400">{currentSeason} NFL Season</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-1 rounded-lg border border-nfl-border overflow-hidden text-xs">
            {(['all', 'scheduled', 'in_progress', 'final'] as const).map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1.5 font-medium transition-colors ${filter === f ? 'bg-nfl-blue text-white' : 'text-gray-400 hover:bg-gray-800'}`}>
                {f === 'in_progress' ? 'Live' : f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1">
            <button onClick={() => setWeek(currentWeek - 1)} disabled={currentWeek <= 1}
              className="w-8 h-8 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-30 flex items-center justify-center text-sm">‹</button>
            <span className="px-3 py-1 bg-nfl-blue/20 border border-nfl-blue/50 rounded-lg text-sm font-medium">Week {currentWeek}</span>
            <button onClick={() => setWeek(currentWeek + 1)} disabled={currentWeek >= 22}
              className="w-8 h-8 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-30 flex items-center justify-center text-sm">›</button>
          </div>
        </div>
      </div>

      {/* Games Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => <GameCardSkeleton key={i} />)}
        </div>
      ) : games.length === 0 ? (
        <div className="card text-center text-gray-500 py-16">
          <p className="text-lg">No {filter !== 'all' ? filter : ''} games for Week {currentWeek}</p>
          <p className="text-sm mt-2">Use the arrows to navigate weeks, or check back once data syncs.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {games.map((game: any) => <GameCard key={game.id} game={game} />)}
        </div>
      )}
    </div>
  );
}

function GameCard({ game }: { game: any }) {
  const isFinal = game.status === 'final';
  const isLive = game.status === 'in_progress';

  return (
    <Link to={`/games/${game.id}`} className="card-hover">
      {/* Status Badge */}
      <div className="flex items-center justify-between mb-3 text-xs">
        <span className={`badge ${isFinal ? 'bg-gray-700 text-gray-300' : isLive ? 'bg-green-900 text-green-300' : 'bg-blue-900/50 text-blue-300'}`}>
          {isFinal ? 'FINAL' : isLive ? '● LIVE' : new Date(game.game_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
        <span className="text-gray-500">{game.broadcast_network}</span>
      </div>

      {/* Teams & Score */}
      <div className="space-y-2">
        <TeamRow abbr={game.away_abbr} name={game.away_team_name} color={game.away_color}
          score={game.away_score} isFinal={isFinal} isLive={isLive} />
        <TeamRow abbr={game.home_abbr} name={game.home_team_name} color={game.home_color}
          score={game.home_score} isFinal={isFinal} isLive={isLive} isHome />
      </div>

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-nfl-border/50 flex justify-between text-xs text-gray-500">
        <span>{game.venue?.split(',')[0] || '—'}</span>
        {game.weather_temp_f && <span>{game.weather_temp_f}°F {game.weather_wind_mph > 10 ? `· ${game.weather_wind_mph}mph` : ''}</span>}
      </div>
    </Link>
  );
}

function TeamRow({ abbr, name, color, score, isFinal, isLive, isHome }: any) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white"
          style={{ backgroundColor: color || '#1a1a2e' }}>
          {abbr?.slice(0, 2)}
        </div>
        <div>
          <span className="text-sm font-medium">{abbr}</span>
          {isHome && <span className="text-xs text-gray-500 ml-1">HOME</span>}
        </div>
      </div>
      {(isFinal || isLive) && score != null ? (
        <span className="text-lg font-bold">{score}</span>
      ) : (
        <span className="text-sm text-gray-500">—</span>
      )}
    </div>
  );
}
