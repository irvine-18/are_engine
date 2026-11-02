"use client";

import { useState } from "react";

import { PortfolioListView } from "./components/PortfolioListView";
import { PortfolioDetailView } from "./components/PortfolioDetailView";

export function PortfolioPage() {
  const [view, setView] = useState<{ mode: "list" } | { mode: "detail"; id: string }>({ mode: "list" });

  if (view.mode === "detail") {
    return <PortfolioDetailView portfolioId={view.id} onBack={() => setView({ mode: "list" })} />;
  }
  return <PortfolioListView onOpen={(id) => setView({ mode: "detail", id })} />;
}
