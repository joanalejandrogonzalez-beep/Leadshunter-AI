import React from "react";
import { Zap } from "lucide-react";

export const HeroBadge: React.FC = () => {
  return (
    <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-navy/80 border border-brand-electric/30 backdrop-blur-md shadow-[0_0_20px_rgba(0,85,255,0.2)] hover:border-brand-electric/60 transition-colors duration-300">
      <span className="flex h-2 w-2 relative">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-cyan opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-electric" />
      </span>
      <span className="text-xs sm:text-sm font-semibold text-white tracking-wide flex items-center gap-1.5">
        <span className="text-yellow-400">⚡</span> Prospección B2B impulsada por IA explicable
      </span>
    </div>
  );
};
