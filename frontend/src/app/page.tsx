'use client';

import React, { useEffect, useState } from 'react';
import { BarChart3, Loader2, Search, ShieldAlert, Users, Zap } from 'lucide-react';
import { fetchTeams } from '../lib/api';

export default function Dashboard() {
  const [teams, setTeams] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setTeams(await fetchTeams());
      } catch (err) {
        console.error('Error loading dashboard data', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const filteredTeams = teams.filter((team) =>
    String(team.name || '').toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#05070d] text-[#e8eaf6] font-sans p-6">
      <nav className="fixed left-0 top-0 h-full w-64 bg-[#0b0f1a] border-r border-[#1a2236] p-4 hidden lg:block">
        <div className="text-2xl font-bold mb-10 flex items-center gap-2">
          <Zap className="text-[#00d4aa]" fill="#00d4aa" />
          <span>KICKDEX</span>
        </div>
        <div className="space-y-4">
          <div className="text-[#8b9ab0] text-xs font-bold uppercase tracking-wider">Terminal</div>
          <button className="w-full flex items-center gap-3 p-3 bg-[#1a2236] text-[#00d4aa] rounded-lg">
            <BarChart3 size={18} />
            <span>Data Analysis</span>
          </button>
          <button className="w-full flex items-center gap-3 p-3 hover:bg-[#1a2236] transition-colors rounded-lg group">
            <Users size={18} className="group-hover:text-[#00d4aa]" />
            <span>Player Scouting</span>
          </button>
          <button className="w-full flex items-center gap-3 p-3 hover:bg-[#1a2236] transition-colors rounded-lg group">
            <ShieldAlert size={18} className="group-hover:text-[#00d4aa]" />
            <span>Referee Profiles</span>
          </button>
        </div>
      </nav>

      <main className="lg:ml-64 space-y-8">
        <header className="flex justify-between items-center bg-[#0b0f1a]/50 backdrop-blur-md sticky top-0 py-4 z-10">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Football Data Terminal</h1>
            <p className="text-[#8b9ab0] text-sm">Teams, historical data, comparators and player scouting.</p>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8b9ab0]" size={18} />
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search team..."
              className="bg-[#0b0f1a] border border-[#1a2236] rounded-full py-2 pl-10 pr-4 w-64 focus:outline-none focus:border-[#00d4aa] transition-all text-sm"
            />
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { label: 'Teams', val: teams.length || '—' },
            { label: 'Leagues', val: new Set(teams.map((team) => team.league).filter(Boolean)).size || '—' },
            { label: 'Modules', val: 'Comparador · H2H · Jugadores' },
          ].map((item, index) => (
            <div key={index} className="bg-[#0b0f1a] border border-[#1a2236] p-6 rounded-2xl">
              <div className="text-[#8b9ab0] text-[10px] font-bold uppercase tracking-widest">{item.label}</div>
              <div className="text-2xl font-mono font-bold mt-2 text-[#00d4aa]">{item.val}</div>
            </div>
          ))}
        </div>

        <section>
          <div className="flex items-center gap-2 mb-6">
            <h2 className="text-xl font-bold">Teams</h2>
            <div className="h-px flex-grow bg-[#1a2236] ml-4"></div>
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-[#8b9ab0]">
              <Loader2 className="animate-spin mb-4" size={32} />
              <p className="text-sm font-medium">Loading football data...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredTeams.slice(0, 60).map((team: any) => (
                <div key={team.id || team.name} className="bg-[#0b0f1a] border border-[#1a2236] p-5 rounded-2xl">
                  <div className="font-semibold text-lg">{team.name}</div>
                  <div className="text-[#8b9ab0] text-sm mt-1">{team.league || 'League pending'}</div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
