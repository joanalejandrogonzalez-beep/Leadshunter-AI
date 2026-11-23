import React from "react";

interface MatchScoreBadgeProps {
  score: number;
}

export const MatchScoreBadge: React.FC<MatchScoreBadgeProps> = ({ score }) => {
  const isHigh = score >= 85;
  const isMedium = score >= 70 && score < 85;

  const colorClasses = isHigh
    ? "bg-brand-neon/15 text-brand-neon border-brand-neon/30 shadow-[0_0_12px_rgba(0,229,190,0.25)]"
    : isMedium
    ? "bg-brand-cyan/15 text-brand-cyan border-brand-cyan/30 shadow-[0_0_12px_rgba(56,189,248,0.25)]"
    : "bg-brand-slate/15 text-brand-slate border-brand-slate/30";

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${colorClasses}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      <span>{score}% Relevancia</span>
    </div>
  );
};
