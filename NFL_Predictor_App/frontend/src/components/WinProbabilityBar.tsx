interface WinProbabilityBarProps {
  homeTeam: string;
  awayTeam: string;
  homeProb: number;
  awayProb: number;
  homeColor?: string;
  awayColor?: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function WinProbabilityBar({
  homeTeam, awayTeam, homeProb, awayProb,
  homeColor = '#013369', awayColor = '#D50A0A',
  size = 'md',
}: WinProbabilityBarProps) {
  const homePct = Math.round(homeProb * 100);
  const awayPct = Math.round(awayProb * 100);
  const height = size === 'lg' ? 'h-8' : size === 'sm' ? 'h-3' : 'h-5';
  const textSize = size === 'lg' ? 'text-base font-bold' : size === 'sm' ? 'text-xs' : 'text-sm';

  return (
    <div className="w-full">
      <div className={`flex items-center justify-between mb-1 ${textSize}`}>
        <span className="font-semibold">{homeTeam}</span>
        <span className="font-semibold">{awayTeam}</span>
      </div>
      <div className={`relative flex rounded-full overflow-hidden ${height}`}>
        <div className="flex items-center justify-center text-white font-bold text-xs transition-all"
          style={{ width: `${homePct}%`, backgroundColor: homeColor }}>
          {size !== 'sm' && `${homePct}%`}
        </div>
        <div className="flex items-center justify-center text-white font-bold text-xs transition-all"
          style={{ width: `${awayPct}%`, backgroundColor: awayColor }}>
          {size !== 'sm' && `${awayPct}%`}
        </div>
      </div>
      <div className={`flex items-center justify-between mt-1 ${size === 'sm' ? 'text-xs' : 'text-sm'} text-gray-400`}>
        <span>{homePct}% HOME</span>
        <span>AWAY {awayPct}%</span>
      </div>
    </div>
  );
}
