"use client";

import React, { useState } from "react";
import { HeroBadge } from "./HeroBadge";
import { HeroHeadline } from "./HeroHeadline";
import { SearchBarCTA } from "./SearchBarCTA";
import { DashboardMockup } from "../preview/DashboardMockup";

export const HeroSection: React.FC = () => {
  const [searchFilter, setSearchFilter] = useState("");

  return (
    <section className="relative pt-32 sm:pt-40 pb-16 sm:pb-24 px-4 sm:px-6 lg:px-8 overflow-hidden">
      <div className="max-w-7xl mx-auto space-y-8 sm:space-y-10">
        
        {/* Top Centered Badge */}
        <div className="flex justify-center">
          <HeroBadge />
        </div>

        {/* Impactful Headline & Subtitle */}
        <HeroHeadline />

        {/* Interactive Search Bar CTA */}
        <SearchBarCTA onSearch={(val) => setSearchFilter(val)} />

        {/* Visual Interactive Preview (Dashboard Mockup) */}
        <DashboardMockup searchFilter={searchFilter} />

      </div>
    </section>
  );
};
