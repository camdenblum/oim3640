import { Link } from 'react-router-dom';
import WinProbabilityBar from './WinProbabilityBar';

interface Game {
  id: number;
  home_team_name: string; home_abbr: string; home_color: string;
  away_team_name: string; away_abbr: string; away_color: string;
  game_date: string; broadcast_network: string;
  venue: string; weather_temp_f?: number; weather_wind_mph?: number;
  home_score?: number; away_score?: number; status: string;
}

interface Prediction {
  home_win_probability: number; away_win_probability: number;
  predicted_home_score: number; predicted_away_score: number;
  predicted_spread: number; confidence_score: number;
}

interface Props { game: Game; prediction?: Prediction; variant?: 'compact' | 'featured'; }

export default function GamePredictionCard({ game, prediction, variant = 'compact' }: Props) {
  const isFinal = game.status === 'final';
  const homeWinProb = prediction?.home_win_probability ?? 0.5;
  const awayWinProb = prediction?.away_win_probability ?? 0.5;

  if (variant === 'featured') {
    return (
      <Link to={`/predict/game/${game.id}`} className="card-hover block">
        <div className="flex items-center justify-between mb-4">
          <div className="text-xs text-nfl-gold font-semibold uppercase tracking-wider">Featured Game</div>
          <div className="text-xs text-gray-500">{game.broadcast_network}</div>
        </div>
        <div className="grid grid-cols-3 gap-4 items-center mb-4">
          <TeamBlock abbr={game.away_abbr} name={game.away_team_name} color={game.away_color}
            score={isFinal ? game.away_score : prediction?.predicted_away_score} isFinal={isFinal} side="away" />
          <div className="text-center">
            {isFinal ? <div className="text-2xl font-bold text-gray-300">FINAL</div>
              : <div className="text-xs text-gray-400">{new Date(game.game_date).toLocaleDateString()}</div>}
            {prediction && !isFinal && (
              <div className="text-xs text-gray-500 mt-1">
                Spread: {prediction.predicted_spread > 0 ? '+' : ''}{prediction.predicted_spread.toFixed(1)}
              </div>
            )}
          </div>
          <TeamBlock abbr={game.home_abbr} name={game.home_team_name} color={game.home_color}
            score={isFinal ? game.home_score : prediction?.predicted_home_score} isFinal={isFinal} side="home" />
        </div>
        {prediction && !isFinal && (
          <WinProbabilityBar homeTeam={game.home_abbr} awayTeam={game.away_abbr}
            homeProb={homeWinProb} awayProb={awayWinProb}
            homeColor={game.home_color} awayColor={game.away_color} size="lg" />
        )}
        {prediction && (
          <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
            <span>Confidence: <span className={prediction.confidence_score > 0.7 ? 'text-green-400' : prediction.confidence_score > 0.55 ? 'text-yellow-400' : 'text-gray-400'}>
              {(prediction.confidence_score * 100).toFixed(0)}%
            </span></span>
            <span>{game.weather_temp_f ? `${game.weather_temp_f}°F` : ''} {game.weather_wind_mph ? `${game.weather_wind_mph}mph wind` : ''}</span>
          </div>
        )}
      </Link>
    );
  }

  return (
    <Link to={`/predict/game/${game.id}`} className="card-hover block">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <TeamLogo abbr={game.away_abbr} color={game.away_color} />
          <span className="font-semibold text-sm">{game.away_abbr}</span>
          {isFinal && <span className="text-lg font-bold">{game.away_score}</span>}
        </div>
        <div className="text-xs text-gray-500 text-center">
          {isFinal ? <span className="text-gray-300 font-medium">FINAL</span>
            : <span>{new Date(game.game_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>}
        </div>
        <div className="flex items-center gap-2">
          {isFinal && <span className="text-lg font-bold">{game.home_score}</span>}
          <span className="font-semibold text-sm">{game.home_abbr}</span>
          <TeamLogo abbr={game.home_abbr} color={game.home_color} />
        </div>
      </div>
      {prediction && !isFinal && (
        <>
          <WinProbabilityBar homeTeam={game.home_abbr} awayTeam={game.away_abbr}
            homeProb={homeWinProb} awayProb={awayWinProb}
            homeColor={game.home_color} awayColor={game.away_color} size="sm" />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{prediction.predicted_away_score.toFixed(0)}–{prediction.predicted_home_score.toFixed(0)}</span>
            {game.weather_temp_f && <span>{game.weather_temp_f}°F</span>}
          </div>
        </>
      )}
    </Link>
  );
}

function TeamBlock({ abbr, name, color, score, isFinal, side }: {
  abbr: string; name: string; color: string; score?: number; isFinal: boolean; side: 'home' | 'away';
}) {
  return (
    <div className={`flex flex-col items-center gap-2 ${side === 'home' ? 'items-end' : 'items-start'}`}>
      <TeamLogo abbr={abbr} color={color} size="lg" />
      <div className="font-semibold text-sm text-center">{abbr}</div>
      {score != null && <div className="text-3xl font-bold">{isFinal ? score : `~${Math.round(score)}`}</div>}
    </div>
  );
}

export function TeamLogo({ abbr, color, size = 'sm' }: { abbr: string; color: string; size?: 'sm' | 'md' | 'lg' }) {
  const sizes = { sm: 'w-8 h-8 text-xs', md: 'w-10 h-10 text-sm', lg: 'w-16 h-16 text-base' };
  return (
    <div className={`${sizes[size]} rounded-full flex items-center justify-center font-bold text-white`}
      style={{ backgroundColor: color || '#1a1a2e' }}>
      {abbr?.slice(0, 2)}
    </div>
  );
}
