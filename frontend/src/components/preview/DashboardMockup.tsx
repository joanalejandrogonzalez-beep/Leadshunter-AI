"use client";

import React, { useMemo } from "react";
import { MOCK_PROSPECTS } from "@/data/mockProspects";
import { MockupHeader } from "./MockupHeader";
import { ProspectRow } from "./ProspectRow";

interface DashboardMockupProps {
  searchFilter: string;
}

export const DashboardMockup: React.FC<DashboardMockupProps> = ({ searchFilter }) => {
  const filteredProspects = useMemo(() => {
    if (!searchFilter.trim()) return MOCK_PROSPECTS;
    const lower = searchFilter.toLowerCase();
    return MOCK_PROSPECTS.filter(
      (p) =>
        p.name.toLowerCase().includes(lower) ||
        p.sector.toLowerCase().includes(lower) ||
        p.city.toLowerCase().includes(lower) ||
        p.signals.some((s) => s.toLowerCase().includes(lower))
    );
  }, [searchFilter]);

  return (
    <div className="relative w-full max-w-5xl mx-auto pt-6 pb-12 sm:pt-10">
      
      {/* Outer ambient glow behind mockup card */}
      <div 
        className="absolute inset-x-12 top-10 h-72 rounded-full opacity-25 blur-[100px] pointer-events-none -z-10"
        style={{
          background: "linear-gradient(90deg, #0055FF 0%, #38BDF8 50%, #00E5BE 100%)",
        }}
      />

      {/* Floating Glassmorphism Container with 3D tilt sensation */}
      <div className="relative rounded-3xl overflow-hidden glass-panel border border-white/15 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.8),0_0_40px_rgba(0,85,255,0.15)] transition-all duration-500 hover:border-brand-electric/40">
        
        {/* Mockup Header */}
        <MockupHeader totalLeads={filteredProspects.length} />

        {/* Table Content */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm">
            <thead className="bg-brand-obsidian/60 text-brand-slate uppercase text-[10px] tracking-wider font-semibold border-b border-white/5">
              <tr>
                <th className="py-3 px-4">Empresa & Sitio Web</th>
                <th className="py-3 px-4">Match Score</th>
                <th className="py-3 px-4 hidden md:table-cell">Señales Comerciales Auditadas</th>
                <th className="py-3 px-4 text-right">Etapa CRM</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredProspects.length > 0 ? (
                filteredProspects.map((prospect) => (
                  <ProspectRow key={prospect.id} prospect={prospect} />
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-brand-slate text-xs">
                    No se encontraron prospectos simulados para &quot;{searchFilter}&quot;. Prueba con &quot;Constructoras&quot; o &quot;Dental&quot;.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Mockup Footer Bar */}
        <div className="p-3 bg-brand-obsidian/80 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between text-xs text-brand-slate gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-brand-cyan" />
            <span>Algoritmo de 5 factores: Encaje, Capacidad, Necesidad, Actividad y Calidad.</span>
          </div>
          <span className="text-[11px] text-brand-muted">
            Mostrando {filteredProspects.length} de {MOCK_PROSPECTS.length} prospectos en Santo Domingo
          </span>
        </div>

      </div>

    </div>
  );
};
