'use client';

interface MoodPoint {
  check_in_date: string;
  mood_score: number;
}

const MOOD_COLORS = ['#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e'];

export default function MoodGraph({ history }: { history: MoodPoint[] }) {
  if (history.length === 0) return null;

  const width = 600;
  const height = 120;
  const pad = { top: 10, bottom: 24, left: 20, right: 20 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const points = history.map((d, i) => ({
    x: pad.left + (i / Math.max(history.length - 1, 1)) * plotW,
    y: pad.top + ((5 - d.mood_score) / 4) * plotH,
    score: d.mood_score,
    date: d.check_in_date,
  }));

  const pathD =
    points.length < 2
      ? ''
      : points.reduce((acc, p, i) => {
          if (i === 0) return `M ${p.x} ${p.y}`;
          const prev = points[i - 1];
          const cpx = (prev.x + p.x) / 2;
          return `${acc} C ${cpx} ${prev.y} ${cpx} ${p.y} ${p.x} ${p.y}`;
        }, '');

  return (
    <div className="overflow-x-auto" role="img" aria-label="Mood history chart for the past 30 days">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full min-w-[280px]">
        {/* Grid lines */}
        {[1, 2, 3, 4, 5].map((score) => {
          const y = pad.top + ((5 - score) / 4) * plotH;
          return (
            <line
              key={score}
              x1={pad.left}
              y1={y}
              x2={width - pad.right}
              y2={y}
              stroke="#EDE8DC"
              strokeWidth="1"
            />
          );
        })}

        {/* Area fill */}
        {pathD && (
          <path
            d={`${pathD} L ${points[points.length - 1].x} ${height - pad.bottom} L ${points[0].x} ${height - pad.bottom} Z`}
            fill="rgba(45, 80, 22, 0.06)"
          />
        )}

        {/* Line */}
        {pathD && (
          <path
            d={pathD}
            fill="none"
            stroke="#2D5016"
            strokeWidth="2"
            strokeLinecap="round"
          />
        )}

        {/* Points */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="4"
            fill={MOOD_COLORS[p.score - 1]}
            stroke="white"
            strokeWidth="1.5"
          >
            <title>{p.date}: {['Really struggling','A bit rough','Okay','Pretty good','Doing great'][p.score - 1]}</title>
          </circle>
        ))}
      </svg>
    </div>
  );
}
