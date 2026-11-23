"use client";

import React, { useState } from "react";
import { Search, ArrowRight, Sparkles, ShieldCheck } from "lucide-react";

interface SearchBarCTAProps {
  onSearch: (query: string) => void;
}

export const SearchBarCTA: React.FC<SearchBarCTAProps> = ({ onSearch }) => {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSearching(true);
    onSearch(query);
    setTimeout(() => setIsSearching(false), 500);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    onSearch(val);
  };

  const handleQuickTagClick = (tag: string) => {
    setQuery(tag);
    onSearch(tag);
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-3">
      {/* Interactive Input Form */}
      <form onSubmit={handleSearchSubmit} className="relative">
        <div className="relative flex flex-col sm:flex-row items-center gap-2 p-1.5 sm:p-2 rounded-2xl glass-panel border border-white/15 shadow-glass focus-within:border-brand-electric/80 focus-within:shadow-electric-glow transition-all duration-300">
          
          {/* Input field with search icon */}
          <div className="relative flex-1 w-full flex items-center pl-3">
            <Search className="w-5 h-5 text-brand-slate shrink-0 mr-2.5" />
            <input
              type="text"
              value={query}
              onChange={handleInputChange}
              placeholder="Ej. Clínicas dentales en Santo Domingo"
              className="w-full bg-transparent text-sm sm:text-base text-white placeholder-brand-muted focus:outline-none py-2"
            />
          </div>

          {/* Primary CTA Button */}
          <button
            type="submit"
            className="w-full sm:w-auto relative inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-btn-gradient text-white text-sm sm:text-base font-semibold border border-brand-electric/50 shadow-electric-sm hover:shadow-electric-glow hover:border-brand-electric transition-all duration-300 shrink-0 group"
          >
            {isSearching ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Analizando...</span>
              </span>
            ) : (
              <>
                <span>Buscar Prospectos Ahora</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Suggested Quick Tags */}
      <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-brand-slate">
        <span className="text-brand-muted">Probar búsqueda rápida:</span>
        <button
          type="button"
          onClick={() => handleQuickTagClick("Constructoras en Santo Domingo")}
          className="px-2.5 py-1 rounded-lg bg-brand-navy/60 hover:bg-brand-navy-light text-slate-300 hover:text-white border border-white/5 transition"
        >
          🏗️ Constructoras
        </button>
        <button
          type="button"
          onClick={() => handleQuickTagClick("Inmobiliarias en Santo Domingo")}
          className="px-2.5 py-1 rounded-lg bg-brand-navy/60 hover:bg-brand-navy-light text-slate-300 hover:text-white border border-white/5 transition"
        >
          🏢 Inmobiliarias
        </button>
        <button
          type="button"
          onClick={() => handleQuickTagClick("Clínica Dental")}
          className="px-2.5 py-1 rounded-lg bg-brand-navy/60 hover:bg-brand-navy-light text-slate-300 hover:text-white border border-white/5 transition"
        >
          🦷 Dentales
        </button>
      </div>

      {/* Trust Subtext */}
      <div className="flex items-center justify-center gap-2 text-xs text-brand-slate pt-1">
        <ShieldCheck className="w-4 h-4 text-brand-electric" />
        <span>Sin tarjeta de crédito • 100 búsquedas de prueba gratis</span>
      </div>
    </div>
  );
};
