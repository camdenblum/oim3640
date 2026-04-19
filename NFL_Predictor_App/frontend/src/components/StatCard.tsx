interface StatCardProps {
  label: string;
  value: string | number;
  rank?: number;
  trend?: 'up' | 'down' | 'neutral';
  color?: string;
  subtitle?: string;
}

export default function StatCard({ label, value, rank, trend, color = 'text-white', subtitle }: StatCardProps) {
  return (
    <div className="card flex flex-col">
      <div className="flex items-start justify-between">
        <div>
          <div className={`text-2xl font-bold ${color}`}>{value}</div>
          {subtitle && <div className="text-xs text-gray-500 mt-0.5">{subtitle}</div>}
          <div className="stat-label">{label}</div>
        </div>
        <div className="flex flex-col items-end gap-1">
          {rank != null && (
            <span className="rank-badge">#{rank}</span>
          )}
          {trend && (
            <span className={trend === 'up' ? 'text-green-400 text-sm' : trend === 'down' ? 'text-red-400 text-sm' : 'text-gray-500 text-sm'}>
              {trend === 'up' ? '▲' : trend === 'down' ? '▼' : '—'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
