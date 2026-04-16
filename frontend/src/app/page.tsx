'use client';

import React, { useEffect, useState } from 'react';
import { Search, BarChart3, Users, Zap, ShieldAlert, Activity, Loader2 } from 'lucide-react';
import { fetchLiveMarket, fetchLiveScores, fetchTeams } from '../lib/api';
import { MatchCard } from '../components/MatchCard';

export default function Dashboard() {
  const [liveMatches, setLiveScores] = useState<any[]>([]);
  const [odds, setOdds] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [scoresData, oddsData] = await Promise.all([
          fetchLiveScores(),
          fetchLiveMarket()
        ]);
        setLiveScores(scoresData);
        setOdds(oddsData);
      } catch (err) {
        console.error("Error loading dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every min
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#05070d] text-[#e8eaf6] font-sans p-6">
      {/* Sidebar */}
      <nav className="fixed left-0 top-0 h-full w-64 bg-[#0b0f1a] border-r border-[#1a2236] p-4 hidden lg:block">
        <div className="text-2xl font-bold mb-10 flex items-center gap-2">
          <Zap className="text-[#00d4aa]" fill="#00d4aa" />
          <span>KICKDEX</span>
        </div>
        <div className="space-y-4">
          <div className="text-[#8b9ab0] text-xs font-bold uppercase tracking-wider">Terminal</div>
          <button className="w-full flex items-center gap-3 p-3 bg-[#1a2236] text-[#00d4aa] rounded-lg">
            <BarChart3 size={18} />
            <span>Market Analysis</span>
          </button>
          <button className="w-full flex items-center gap-3 p-3 hover:bg-[#1a2236] transition-colors rounded-lg group">
            <Users size={18} className="group-hover:text-[#00d4aa]" />
            <span>Player Scouting</span>
          </button>
          <button className="w-full flex items-center gap-3 p-3 hover:bg-[#1a2236] transition-colors rounded-lg group">
            <ShieldAlert size={18} className="group-hover:text-[#00d4aa]" />
            <span>Backtesting Lab</span>
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="lg:ml-64 space-y-8">
        <header className="flex justify-between items-center bg-[#0b0f1a]/50 backdrop-blur-md sticky top-0 py-4 z-10">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Market Intelligence</h1>
            <p className="text-[#8b9ab0] text-sm flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00d4aa] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00d4aa]"></span>
              </span>
              Connected to Terminal Core — Real-Time Feed
            </p>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8b9ab0]" size={18} />
            <input 
              type="text" 
              placeholder="Search team or player..." 
              className="bg-[#0b0f1a] border border-[#1a2236] rounded-full py-2 pl-10 pr-4 w-64 focus:outline-none focus:border-[#00d4aa] transition-all text-sm"
            />
          </div>
        </header>

        {/* Global Market Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: 'Market Matches', val: odds.length || '—', color: '#00d4aa' },
            { label: 'Live Events', val: liveMatches.length || '0', color: '#5bd6ff' },
            { label: 'Avg System EV', val: '+4.2%', color: '#f5b93c' },
            { label: 'Data Accuracy', val: '99.9%', color: '#00d4aa' }
          ].map((s, i) => (
            <div key={i} className="bg-[#0b0f1a] border border-[#1a2236] p-6 rounded-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <Activity size={48} />
              </div>
              <div className="text-[#8b9ab0] text-[10px] font-bold uppercase tracking-widest">{s.label}</div>
              <div className="text-3xl font-mono font-bold mt-2" style={{ color: s.color }}>{s.val}</div>
            </div>
          ))}
        </div>

        {/* Live Grid */}
        <section>
          <div className="flex items-center gap-2 mb-6">
            <h2 className="text-xl font-bold">Featured Opportunities</h2>
            <div className="h-px flex-grow bg-[#1a2236] ml-4"></div>
          </div>
          
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-[#8b9ab0]">
              <Loader2 className="animate-spin mb-4" size={32} />
              <p className="text-sm font-medium">Syncing with global betting markets...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {odds.map((o: any, i: number) => {
                const b365 = o.bookmakers.find((b: any) => b.key === 'bet365');
                const outcomes = b365?.markets[0]?.outcomes || [];
                return (
                  <MatchCard 
                    key={i}
                    home={o.home_team}
                    away={o.away_team}
                    odds={{
                      h: outcomes.find((x: any) => x.name === o.home_team)?.price || 0,
                      d: outcomes.find((x: any) => x.name === 'Draw')?.price || 0,
                      a: outcomes.find((x: any) => x.name === o.away_team)?.price || 0
                    }}
                  />
                );
              })}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
