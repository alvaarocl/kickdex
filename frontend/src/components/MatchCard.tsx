import React from 'react';
import { Activity } from 'lucide-react';

interface MatchCardProps {
  home: string;
  away: string;
  score?: string;
  minute?: number;
  odds?: { h: number; d: number; a: number };
}

export const MatchCard: React.FC<MatchCardProps> = ({ home, away, score, minute, odds }) => {
  return (
    <div className="bg-[#0b0f1a] border border-[#1a2236] p-5 rounded-2xl hover:border-[#00d4aa] transition-all group">
      <div className="flex justify-between items-start mb-4">
        <span className="text-[#8b9ab0] text-[10px] font-bold uppercase tracking-widest flex items-center gap-1">
          {minute ? (
            <>
              <Activity size={12} className="text-[#00d4aa] animate-pulse" />
              Live {minute}'
            </>
          ) : 'Scheduled'}
        </span>
        {score && <span className="text-[#00d4aa] font-mono font-bold">{score}</span>}
      </div>
      
      <div className="space-y-2 mb-6">
        <div className="flex justify-between items-center">
          <span className="font-semibold text-lg">{home}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="font-semibold text-lg">{away}</span>
        </div>
      </div>

      {odds && (
        <div className="grid grid-cols-3 gap-2">
          {[
            { label: '1', val: odds.h },
            { label: 'X', val: odds.d },
            { label: '2', val: odds.a }
          ].map((o, i) => (
            <div key={i} className="bg-[#1a2236] p-2 rounded-lg text-center group-hover:bg-[#252e44] transition-colors">
              <div className="text-[#8b9ab0] text-[9px] font-bold">{o.label}</div>
              <div className="text-sm font-mono font-bold text-[#e8eaf6]">{o.val.toFixed(2)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
