"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { Alert, Stack } from "@mui/material";
import AssessmentIcon from "@mui/icons-material/Assessment";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageLoadingOverlay } from "@/components/feedback/PageLoadingOverlay";
import { usePortfolioList, useRuns } from "@/lib/api/hooks";

import { RunCard, type RunRow } from "./components/RunCard";

export function ScrResultsPage() {
  const router = useRouter();
  const { data: runs, isLoading: isLoadingRuns } = useRuns();
  const { data: portfolios, isLoading: isLoadingPortfolios } = usePortfolioList();
  const isLoading = isLoadingRuns || isLoadingPortfolios;

  const rows: RunRow[] = useMemo(() => {
    const portfolioNames = new Map((portfolios ?? []).map((p) => [p.id, p.name]));
    return (runs ?? [])
      .map((run) => ({
        id: run.id,
        portfolioName: portfolioNames.get(run.portfolio_id) ?? run.portfolio_id,
        status: run.status,
        createdAt: run.created_at,
      }))
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  }, [runs, portfolios]);

  return (
    <Stack spacing={2.5}>
      <PageHeader
        section="Asset Market Risk"
        title="SCR Results"
        description="Every portfolio SCR run, across every portfolio — open one to see its full SCR breakdown, scenario impacts and positions."
        icon={<AssessmentIcon fontSize="small" />}
        statusLabel="Live"
      />

      <PageLoadingOverlay loading={isLoading} label="SCR Results">
        {rows.length === 0 ? (
          <Alert severity="info">No portfolio runs yet — start one from Portfolio Construction.</Alert>
        ) : (
          <Stack spacing={1.5}>
            {rows.map((row) => (
              <RunCard key={row.id} run={row} onViewResults={() => router.push(`/assets/results?run_id=${row.id}`)} />
            ))}
          </Stack>
        )}
      </PageLoadingOverlay>
    </Stack>
  );
}
