import React from "react";

export const BackgroundMesh: React.FC = () => {
  return (
    <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden bg-brand-obsidian">
      {/* Mesh Glow 1: Top Center Electric Blue */}
      <div 
        className="absolute top-[-15%] left-1/2 -translate-x-1/2 w-[700px] h-[500px] sm:w-[1000px] sm:h-[600px] rounded-full opacity-30 blur-[130px]"
        style={{
          background: "radial-gradient(circle, #0055FF 0%, #0B1329 70%, transparent 100%)",
        }}
      />

      {/* Mesh Glow 2: Cyan Ambient Highlight for Headline */}
      <div 
        className="absolute top-[20%] left-[20%] w-[450px] h-[350px] rounded-full opacity-15 blur-[120px]"
        style={{
          background: "radial-gradient(circle, #38BDF8 0%, #050B14 70%, transparent 100%)",
        }}
      />

      {/* Mesh Glow 3: Subtle Deep Navy Floor behind Mockup */}
      <div 
        className="absolute top-[55%] right-[15%] w-[550px] h-[450px] rounded-full opacity-20 blur-[140px]"
        style={{
          background: "radial-gradient(circle, #0055FF 0%, #0B1329 60%, transparent 100%)",
        }}
      />

      {/* Subtle Grid Overlay for precision radar aesthetic */}
      <div 
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: "linear-gradient(to right, #FFFFFF 1px, transparent 1px), linear-gradient(to bottom, #FFFFFF 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
    </div>
  );
};
