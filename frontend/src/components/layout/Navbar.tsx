"use client";

import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Menu, X, Sparkles } from "lucide-react";

export const Navbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
        <nav className="glass-panel rounded-2xl px-4 sm:px-6 py-3 flex items-center justify-between shadow-glass">
          
          {/* Brand Logo & Isotipo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-navy via-brand-navy-light to-brand-electric p-[1px] shadow-electric-sm group-hover:shadow-electric-glow transition-all duration-300">
              <div className="w-full h-full bg-brand-obsidian rounded-[11px] flex items-center justify-center overflow-hidden">
                <Image
                  src="/isotipo.png"
                  alt="LeadHunter AI Isotipo"
                  width={28}
                  height={28}
                  className="w-7 h-7 object-contain group-hover:scale-105 transition-transform duration-300"
                  priority
                />
              </div>
            </div>
            <div className="flex items-baseline">
              <span className="font-brand text-lg sm:text-xl font-bold tracking-tight text-white">
                Lead<span className="text-gradient-electric">Hunter</span>
              </span>
              <span className="ml-1 text-xs font-semibold bg-brand-electric/20 text-brand-cyan px-1.5 py-0.5 rounded-md border border-brand-electric/40">
                AI
              </span>
            </div>
          </Link>

          {/* Center Navigation Links (Desktop) */}
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-brand-slate">
            <Link 
              href="#features" 
              className="hover:text-white transition-colors duration-200"
            >
              Features
            </Link>
            <Link 
              href="#scoring" 
              className="hover:text-white transition-colors duration-200 flex items-center gap-1.5"
            >
              <span>Scoring System</span>
              <span className="w-1.5 h-1.5 rounded-full bg-brand-neon animate-pulse" />
            </Link>
            <Link 
              href="#pricing" 
              className="hover:text-white transition-colors duration-200"
            >
              Pricing
            </Link>
            <Link 
              href="#docs" 
              className="hover:text-white transition-colors duration-200"
            >
              Docs
            </Link>
          </div>

          {/* Right Action Buttons */}
          <div className="hidden sm:flex items-center gap-3">
            <Link
              href="/login"
              className="text-xs sm:text-sm font-semibold text-brand-slate hover:text-white px-3.5 py-2 rounded-xl transition-colors duration-200"
            >
              Iniciar Sesión
            </Link>
            
            <Link
              href="#beta"
              className="relative inline-flex items-center gap-2 px-4 py-2 text-xs sm:text-sm font-semibold text-white rounded-xl bg-btn-gradient border border-brand-electric/50 shadow-electric-sm hover:shadow-electric-glow hover:border-brand-electric transition-all duration-300 group"
            >
              <span>Probar Beta Gratis</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          {/* Mobile Hamburger Button */}
          <div className="flex sm:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-brand-slate hover:text-white focus:outline-none"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

        </nav>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="sm:hidden max-w-7xl mx-auto px-4 pt-2">
          <div className="glass-panel rounded-2xl p-4 space-y-3 shadow-glass">
            <Link 
              href="#features" 
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm font-medium text-brand-slate hover:text-white"
            >
              Features
            </Link>
            <Link 
              href="#scoring" 
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm font-medium text-brand-slate hover:text-white"
            >
              Scoring System
            </Link>
            <Link 
              href="#pricing" 
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm font-medium text-brand-slate hover:text-white"
            >
              Pricing
            </Link>
            <Link 
              href="#docs" 
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm font-medium text-brand-slate hover:text-white"
            >
              Docs
            </Link>
            <div className="pt-2 border-t border-white/10 flex flex-col gap-2">
              <Link
                href="/login"
                className="w-full text-center py-2 text-sm text-brand-slate hover:text-white font-semibold"
              >
                Iniciar Sesión
              </Link>
              <Link
                href="#beta"
                className="w-full text-center py-2.5 text-sm font-semibold text-white rounded-xl bg-btn-gradient border border-brand-electric/50"
              >
                Probar Beta Gratis
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
