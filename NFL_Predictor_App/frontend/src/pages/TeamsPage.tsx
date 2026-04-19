import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { endpoints } from '../utils/api';
import { CardSkeleton } from '../components/LoadingSkeleton';
import { formatRecord } from '../utils/stats';

const CONFERENCES = ['All', 'AFC', 'NFC'];
const DIVISIONS = ['All', 'East', 'North', 'South', 'West'];

export default function TeamsPage() {
  const [conference, setConference] = useState('All');
  const [division, setDivision] = useState('All');

  const { data: res, isLoading } = useQuery({
    queryKey: ['teams'],
    queryFn: () => endpoints.teams.all(),
  });

  const teams: any[] = (res?.data || []).filter((t: any) => {
    if (conference !== 'All' && t.conference !== conference) return false;
    if (division !== 'All' && !t.division?.includes(division)) return false;
    return true;
  });

  const byConf = teams.reduce((acc: any, t: any) => {
    const key = t.conference || 'Unknown';
    if (!acc[key]) acc[key] = {};
    const div = t.division || 'Unknown Division';
    if (!acc[key][div]) acc[key][div] = [];
    acc[key][div].push(t);
    return acc;
  }, {});

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">Teams</h1>
        <div className="flex gap-2 flex-wrap">
          <FilterGroup options={CONFERENCES} value={conference} onChange={setConference} />
          <FilterGroup options={DIVISIONS} value={division} onChange={setDivision} />
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : teams.length === 0 ? (
        <div className="card text-center text-gray-500 py-12">
          <p className="text-lg">No teams found.</p>
          <p className="text-sm mt-2">Teams sync automatically from ESPN on startup. Check the backend logs if this persists.</p>
        </div>
      ) : (
        Object.entries(byConf).sort().map(([conf, divs]: any) => (
          <section key={conf}>
            <h2 className="text-lg font-semibold text-nfl-gold mb-4">{conf} Conference</h2>
            {Object.entries(divs).sort().map(([div, divTeams]: any) => (
              <div key={div} className="mb-6">
                <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">{div}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {divTeams.map((team: any) => (
                    <TeamCard key={team.id} team={team} />
                  ))}
                </div>
              </div>
            ))}
          </section>
        ))
      )}
    </div>
  );
}

function TeamCard({ team }: { team: any }) {
  const wins = Number(team.wins || 0);
  const losses = Number(team.losses || 0);
  const eloChange = team.elo_rating ? Math.round(team.elo_rating - 1500) : 0;

  return (
    <Link to={`/teams/${team.id}`} className="card-hover group">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-12 h-12 rounded-full flex items-center justify-center font-black text-white text-sm transition-transform group-hover:scale-110"
          style={{ backgroundColor: team.primary_color || '#1a1a2e' }}>
          {team.abbreviation}
        </div>
        <div>
          <div className="font-semibold text-sm">{team.name}</div>
          <div className="text-xs text-gray-400">{team.city}</div>
        </div>
      </div>
      <div className="flex items-center justify-between text-sm">
        <span className="font-bold text-lg">{formatRecord(wins, losses)}</span>
        <div className="text-right">
          <div className="text-xs text-gray-400">Elo</div>
          <div className={`text-xs font-medium ${eloChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {Math.round(team.elo_rating || 1500)} {eloChange !== 0 && `(${eloChange > 0 ? '+' : ''}${eloChange})`}
          </div>
        </div>
      </div>
      <div className="mt-2 h-1 rounded-full bg-gray-700">
        <div className="h-1 rounded-full transition-all"
          style={{ width: `${wins + losses > 0 ? (wins / (wins + losses)) * 100 : 50}%`, backgroundColor: team.primary_color || '#013369' }} />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-xs text-gray-500">{team.home_stadium || 'TBD'}</span>
        <span className={`text-xs font-medium ${wins > losses ? 'text-green-400' : wins < losses ? 'text-red-400' : 'text-gray-400'}`}>
          {wins + losses > 0 ? ((wins / (wins + losses)) * 100).toFixed(0) + '%' : '—'}
        </span>
      </div>
    </Link>
  );
}

function FilterGroup({ options, value, onChange }: { options: string[]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex rounded-lg border border-nfl-border overflow-hidden">
      {options.map(opt => (
        <button key={opt} onClick={() => onChange(opt)}
          className={`px-3 py-1.5 text-xs font-medium transition-colors ${value === opt ? 'bg-nfl-blue text-white' : 'text-gray-400 hover:bg-gray-800'}`}>
          {opt}
        </button>
      ))}
    </div>
  );
}
