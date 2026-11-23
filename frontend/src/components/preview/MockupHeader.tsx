import React from "react";
import { SlidersHorizontal, Download, Sparkles, Database } from "lucide-react";

interface MockupHeaderProps {
  totalLeads: number;
}

export const MockupHeader: React.FC<MockupHeaderProps> = ({ totalLeads }) => {
  return (
    <div className="p-4 sm:p-5 border-b border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-brand-navy/90">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="flex h-2.5 w-2.5 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-neon opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-brand-neon" />
          </span>
          <span className="text-xs sm:text-sm font-bold text-white font-brand">
            Pipeline de Prospectos Calificados
          </span>
        </div>
        <span className="text-[11px] font-semibold bg-brand-electric/20 text-brand-cyan border border-brand-electric/30 px-2 py-0.5 rounded-full">
          {totalLeads} Leads Verificados
        </span>
      </div>

      <div className="flex items-center gap-2 text-xs">
        <button 
          type="button" 
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-obsidian/80 hover:bg-brand-navy-light text-brand-slate hover:text-white border border-white/10 transition"
        >
          <SlidersHorizontal className="w-3.5 h-3.5 text-brand-muted" />
          <span>Filtros (Score ≥ 70)</span>
        </button>
        <button 
          type="button" 
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 font-semibold transition"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Exportar .xlsx</span>
        </button>
      </div>
    </div>
  );
};
