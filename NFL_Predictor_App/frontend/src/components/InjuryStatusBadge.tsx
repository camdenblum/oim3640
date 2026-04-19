import { getInjuryStatusColor } from '../utils/stats';

export default function InjuryStatusBadge({ status }: { status: string }) {
  if (!status || status === 'Active') return null;
  return (
    <span className={`badge ${getInjuryStatusColor(status)}`}>
      {status}
    </span>
  );
}
