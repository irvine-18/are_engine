"use client";

import { useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Alert, Box, Button, Stack, Tab, Tabs } from "@mui/material";
import AssessmentIcon from "@mui/icons-material/Assessment";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageLoadingOverlay } from "@/components/feedback/PageLoadingOverlay";
import { useExportRun, usePortfolio, usePositions, useRun, useRunPositions, useRunSummary } from "@/lib/api/hooks";
import { RunHeader } from "./components/RunHeader";
import { KpiRow } from "./components/KpiRow";
import { WaterfallAndImpact } from "./components/WaterfallAndImpact";
import { GroupedResultsTab } from "./components/GroupedResultsTab";
import { MaturityBucketsTab } from "./components/MaturityBucketsTab";
import { CashflowsTab } from "./components/CashflowsTab";
import { PositionsResultsTab } from "./components/PositionsResultsTab";
import { joinPositionResults } from "./utils/joinResults";
import { groupResults } from "./utils/groupResults";

export function ResultsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const runId = searchParams.get("run_id");
  const [tab, setTab] = useState(0);
  const [drillGroup, setDrillGroup] = useState<string | null>(null);

  const { data: run, isLoading: isLoadingRun, isError: isRunError } = useRun(runId ?? undefined);
  const { data: summary, isLoading: isLoadingSummary } = useRunSummary(runId ?? undefined);
  const { data: positionResults, isLoading: isLoadingPositions } = useRunPositions(runId ?? undefined);
  const { data: portfolio } = usePortfolio(run?.portfolio_id);
  const { data: portfolioPositions } = usePositions(run?.portfolio_id);
  const exportRun = useExportRun();

  const enrichedRows = useMemo(
    () => joinPositionResults(positionResults ?? [], portfolioPositions ?? []),
    [positionResults, portfolioPositions],
  );
  const byModellingClass = useMemo(() => groupResults(enrichedRows, (r) => r.modellingClass), [enrichedRows]);

  const backToScrResults = (
    <Button startIcon={<ArrowBackIcon fontSize="small" />} size="small" onClick={() => router.push("/assets/runs")}>
      Back to SCR Results
    </Button>
  );

  if (!runId) {
    return (
      <Stack spacing={2.5}>
        <PageHeader
          section="Asset Market Risk"
          title="Portfolio Results"
          description="SCR breakdown, scenario impacts, buckets and positions for a completed portfolio run."
          icon={<AssessmentIcon fontSize="small" />}
          statusLabel="Live"
          actions={backToScrResults}
        />
        <Alert
          severity="info"
          action={
            <Button color="inherit" size="small" onClick={() => router.push("/assets/portfolio")}>
              Go to Portfolio Construction
            </Button>
          }
        >
          No run selected — start or re-run a portfolio run from the Portfolio Construction page, then come back here.
        </Alert>
      </Stack>
    );
  }

  const isLoading = isLoadingRun || isLoadingSummary || isLoadingPositions;

  if (isRunError || (!isLoading && (!run || !summary))) {
    return (
      <Stack spacing={2.5}>
        <PageHeader
          section="Asset Market Risk"
          title="Portfolio Results"
          description="SCR breakdown, scenario impacts, buckets and positions for a completed portfolio run."
          icon={<AssessmentIcon fontSize="small" />}
          statusLabel="Live"
          actions={backToScrResults}
        />
        <Alert severity="error">No run found for id &quot;{runId}&quot;.</Alert>
      </Stack>
    );
  }

  if (isLoading || !run || !summary) {
    return (
      <Stack spacing={2.5}>
        <PageHeader
          section="Asset Market Risk"
          title="Portfolio Results"
          description="SCR breakdown, scenario impacts, buckets and positions for a completed portfolio run."
          icon={<AssessmentIcon fontSize="small" />}
          statusLabel="Live"
          actions={backToScrResults}
        />
        <PageLoadingOverlay loading label="SCR Results" minHeight={400}>
          <div />
        </PageLoadingOverlay>
      </Stack>
    );
  }

  return (
    <Stack spacing={2.5}>
      <PageHeader
        section="Asset Market Risk"
        title="Portfolio Results"
        description="SCR breakdown, scenario impacts, buckets and positions for a completed portfolio run."
        icon={<AssessmentIcon fontSize="small" />}
        statusLabel="Live"
        actions={backToScrResults}
      />

      <RunHeader
        run={run}
        summary={summary}
        portfolio={portfolio}
        onExport={() => exportRun.mutate(run.id, { onSuccess: (result) => window.open(result.download_url, "_blank") })}
        exporting={exportRun.isPending}
      />

      <KpiRow summary={summary} />
      <WaterfallAndImpact summary={summary} byModellingClass={byModellingClass} />

      {drillGroup && (
        <Alert severity="info" onClose={() => setDrillGroup(null)}>
          Filtered context: <strong>{drillGroup}</strong> — in the full build this would filter the Positions tab.
        </Alert>
      )}

      <Tabs value={tab} onChange={(_, v) => setTab(v)}>
        <Tab label="Grouped" />
        <Tab label="Maturity buckets" />
        <Tab label="Cashflows" />
        <Tab label="Positions" />
      </Tabs>

      <Box>
        {tab === 0 && <GroupedResultsTab rows={enrichedRows} onDrill={setDrillGroup} />}
        {tab === 1 && <MaturityBucketsTab rows={enrichedRows} asOf={new Date(run.created_at)} />}
        {tab === 2 && <CashflowsTab />}
        {tab === 3 && <PositionsResultsTab rows={enrichedRows} />}
      </Box>
    </Stack>
  );
}
