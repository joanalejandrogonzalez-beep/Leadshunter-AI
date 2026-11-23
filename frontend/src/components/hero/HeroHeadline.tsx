import React from "react";

export const HeroHeadline: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto text-center space-y-5">
      <h1 className="font-brand text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.12]">
        Encuentra y Califica{" "}
        <span className="text-gradient-electric inline-block">
          Prospectos B2B
        </span>{" "}
        en Segundos, no en Días.
      </h1>

      <p className="max-w-2xl mx-auto text-base sm:text-lg lg:text-xl text-brand-slate font-normal leading-relaxed">
        LeadHunter AI analiza señales comerciales, puntúa la relevancia de cada empresa 
        y te entrega datos limpios y deduplicados listos para tu CRM.
      </p>
    </div>
  );
};
