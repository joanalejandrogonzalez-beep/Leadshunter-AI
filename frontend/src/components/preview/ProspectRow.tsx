"use client";

import React, { useState } from "react";
import Image from "next/image";
import { ExternalLink, MapPin, CheckCircle2 } from "lucide-react";
import { Prospect } from "@/data/mockProspects";
import { MatchScoreBadge } from "./MatchScoreBadge";

interface ProspectRowProps {
  prospect: Prospect;
}

export const ProspectRow: React.FC<ProspectRowProps> = ({ prospect }) => {
  const [stage, setStage] = useState<"Frío" | "Templado" | "Caliente">(prospect.crmStage);

  return (
    <tr className="border-b border-white/5 hover:bg-white/[0.03] transition-colors duration-200">
      
      {/* Empresa & Verificación con Isotipo */}
      <td className="py-3.5 px-4">
        <div className="flex items-center gap-3">
          <div className="relative w-8 h-8 rounded-lg bg-brand-obsidian border border-brand-electric/40 p-1 flex items-center justify-center shrink-0 shadow-[0_0_10px_rgba(0,85,255,0.2)]">
            <Image
              src="/isotipo.png"
              alt="Verificado"
              width={22}
              height={22}
              className="w-5 h-5 object-contain"
            />
            {prospect.verified && (
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-brand-neon rounded-full border-2 border-brand-navy flex items-center justify-center" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-1.5 font-semibold text-white text-sm">
              <span>{prospect.name}</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-brand-slate mt-0.5">
              <a
                href={`https://${prospect.website}`}
                target="_blank"
                rel="noreferrer"
                className="hover:text-brand-cyan transition-colors flex items-center gap-1"
              >
                <span>{prospect.website}</span>
                <ExternalLink className="w-3 h-3 text-brand-muted" />
              </a>
              <span>•</span>
              <span className="flex items-center gap-0.5 text-brand-muted">
                <MapPin className="w-3 h-3" />
                {prospect.city}
              </span>
            </div>
          </div>
        </div>
      </td>

      {/* Match Score */}
      <td className="py-3.5 px-4 whitespace-nowrap">
        <MatchScoreBadge score={prospect.matchScore} />
      </td>

      {/* Señales Detectadas */}
      <td className="py-3.5 px-4 hidden md:table-cell">
        <div className="flex flex-wrap gap-1.5">
          {prospect.signals.map((sig, idx) => (
            <span
              key={idx}
              className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-brand-obsidian/70 text-brand-slate border border-white/10"
            >
              {sig}
            </span>
          ))}
        </div>
      </td>

      {/* Etapas Rápidas de CRM */}
      <td className="py-3.5 px-4 text-right whitespace-nowrap">
        <div className="inline-flex rounded-lg p-0.5 bg-brand-obsidian border border-white/10">
          {(["Frío", "Templado", "Caliente"] as const).map((s) => {
            const isActive = stage === s;
            const activeStyle =
              s === "Caliente"
                ? "bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-[0_0_10px_rgba(244,63,94,0.3)]"
                : s === "Templado"
                ? "bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-[0_0_10px_rgba(245,158,11,0.3)]"
                : "bg-blue-500/20 text-blue-300 border-blue-500/40 shadow-[0_0_10px_rgba(59,130,246,0.3)]";

            return (
              <button
                key={s}
                type="button"
                onClick={() => setStage(s)}
                className={`px-2 py-1 text-[11px] font-semibold rounded-md border transition-all duration-200 ${
                  isActive
                    ? activeStyle
                    : "border-transparent text-brand-muted hover:text-white"
                }`}
              >
                {s}
              </button>
            );
          })}
        </div>
      </td>

    </tr>
  );
};
