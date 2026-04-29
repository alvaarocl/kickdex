import React from 'react';
import { Activity } from 'lucide-react';

interface MatchCardProps {
  home: string;
  away: string;
  score?: string;
  minute?: number;
}

export const MatchCard: React.FC<MatchCardProps> = ({ home, away, score, minute }) => {
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
      <div className="text-[#8b9ab0] text-xs">Datos históricos disponibles en el comparador</div>
    </div>
  );
};
