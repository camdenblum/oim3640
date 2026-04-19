import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { endpoints } from '../utils/api';
import { Skeleton } from '../components/LoadingSkeleton';

export default function SeasonProjectionsPage() {
  const { data: playoffsRes, isLoading } = useQuery({
    queryKey: ['playoff-probabilities'],
    queryFn: () => endpoints.predictions.playoffs(),
  });

  const teams: any[] = playoffsRes?.data || [];
  const afc = teams.filter(t => t.conference === 'AFC').sort((a, b) => b.wins - a.wins);
  const nfc = teams.filter(t => t.conference === 'NFC').sort((a, b) => b.wins - a.wins);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Season Projections</h1>
        <p className="text-gray-400 text-sm mt-1">Playoff probability based on Elo ratings and current record</p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ConferenceTable conf="AFC" teams={afc} />
          <ConferenceTable conf="NFC" teams={nfc} />
        </div>
      )}

      <div className="card text-sm text-gray-400 space-y-1">
        <p><span className="text-white font-medium">Methodology:</span> Playoff probability is estimated from current W-L record, Elo rating, and remaining schedule strength.</p>
        <p>Elo ratings update after every game using a K-factor of 20 with a 65-point home field advantage.</p>
        <p>Walk-forward ML models retrain weekly — accuracy improves as the season progresses.</p>
      </div>
    </div>
  );
}

function ConferenceTable({ conf, teams }: { conf: string; teams: any[] }) {
  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4 text-nfl-gold">{conf}</h2>
      <div className="space-y-2">
        {teams.map((team, i) => {
          const prob = team.playoff_probability || 0;
          const probPct = Math.round(prob * 100);
          return (
            <div key={team.id} className="flex items-center gap-3 py-2 border-b border-nfl-border/30 last:border-0">
              <span className="w-5 text-xs text-gray-500 font-mono">{i + 1}</span>
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white"
                style={{ backgroundColor: team.primary_color || '#013369' }}>
                {team.abbreviation?.slice(0, 2)}
              </div>
              <div className="flex-1 min-w-0">
                <Link to={`/teams/${team.id}`} className="text-sm font-medium hover:text-nfl-gold block truncate">{team.name}</Link>
                <span className="text-xs text-gray-400">{team.wins || 0}–{team.losses || 0} · Elo {Math.round(team.elo || 1500)}</span>
              </div>
              <div className="text-right min-w-[70px]">
                <div className={`text-sm font-bold ${probPct >= 70 ? 'text-green-400' : probPct >= 40 ? 'text-yellow-400' : 'text-gray-400'}`}>
                  {probPct}%
                </div>
                <div className="text-xs text-gray-500">Playoff</div>
              </div>
              <div className="w-20 h-1.5 bg-gray-700 rounded-full">
                <div className="h-1.5 rounded-full transition-all"
                  style={{ width: `${probPct}%`, backgroundColor: probPct >= 70 ? '#4ade80' : probPct >= 40 ? '#facc15' : '#6b7280' }} />
              </div>
            </div>
          );
        })}
        {teams.length === 0 && (
          <p className="text-center text-gray-500 text-sm py-4">
            Playoff probabilities calculate once team data is loaded.
          </p>
        )}
      </div>
    </div>
  );
}
