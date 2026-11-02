import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Box, Button, Chip, IconButton, Snackbar, Stack, Typography } from "@mui/material";
import FolderIcon from "@mui/icons-material/Folder";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";

import { PageLoadingOverlay } from "@/components/feedback/PageLoadingOverlay";
import { TemplatePicker } from "@/components/economicTemplates/TemplatePicker";
import { useEconomicTemplates } from "@/stores/economicTemplates";
import { usePortfolio, usePositions, useStartRun } from "@/lib/api/hooks";
import { toPortfolioSummary, toPositionRow } from "@/lib/api/portfolioAdapters";
import { fmtDate, fmtMoney } from "@/lib/format";
import { UploadPositionsPanel } from "./UploadPositionsPanel";
import { PositionsList } from "./PositionsList";
import { RunPanel } from "./RunPanel";
import { RunProgressDialog } from "./RunProgressDialog";

export function PortfolioDetailView({ portfolioId, onBack }: { portfolioId: string; onBack: () => void }) {
  const router = useRouter();
  const { data: portfolioData, isLoading: portfolioLoading } = usePortfolio(portfolioId);
  const { data: positionsData } = usePositions(portfolioId);
  const portfolio = portfolioData ? toPortfolioSummary(portfolioData) : undefined;
  const positions = (positionsData ?? []).map(toPositionRow);

  const startRun = useStartRun(portfolioId);
  const { activeTemplate } = useEconomicTemplates();
  // Prices against the active template's own last run, same as Single Asset
  // (`SingleAssetPage.tsx`'s `curveRunId`) -- never re-runs Smith-Wilson here.
  const curveRunId = activeTemplate?.lastRun?.curveRunId ?? null;

  const [runDialogOpen, setRunDialogOpen] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | undefined>();
  const [activeRunId, setActiveRunId] = useState<string | undefined>();
  const [snackbar, setSnackbar] = useState<string | null>(null);

  if (portfolioLoading) {
    return (
      <PageLoadingOverlay loading label="Portfolio Construction" minHeight={400}>
        <div />
      </PageLoadingOverlay>
    );
  }

  if (!portfolio) {
    return (
      <Stack spacing={2}>
        <Alert severity="warning">This portfolio no longer exists.</Alert>
        <Box>
          <Button startIcon={<ArrowBackIcon />} onClick={onBack}>
            Back to portfolios
          </Button>
        </Box>
      </Stack>
    );
  }

  return (
    <Stack spacing={2.5} sx={{ minHeight: "calc(100vh - 220px)" }}>
      <Stack direction="row" spacing={1} alignItems="center">
        <IconButton size="small" onClick={onBack} aria-label="back to portfolios">
          <ArrowBackIcon fontSize="small" />
        </IconButton>
        <Typography variant="overline" color="text.secondary">
          Asset Market Risk · Portfolio Construction
        </Typography>
      </Stack>

      <TemplatePicker />

      <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between" alignItems={{ md: "center" }}>
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Box
            sx={{
              display: "grid",
              placeItems: "center",
              width: 36,
              height: 36,
              borderRadius: 2,
              border: 1,
              borderColor: "divider",
              bgcolor: "background.paper",
              color: "primary.main",
              flexShrink: 0,
            }}
          >
            <FolderIcon fontSize="small" />
          </Box>
          <Typography variant="h5">{portfolio.name}</Typography>
        </Stack>
        <Stack direction="row" spacing={1}>
          <Chip label={`${portfolio.positionCount} positions`} variant="outlined" />
          <Chip label={`Total MV ${fmtMoney(portfolio.totalMarketValue, portfolio.currency, true)}`} variant="outlined" />
          <Chip
            label={portfolio.lastRunAt ? `Last run ${fmtDate(portfolio.lastRunAt)}` : "Never run"}
            variant="outlined"
            color={portfolio.lastRunAt ? "default" : "warning"}
          />
        </Stack>
      </Stack>

      <UploadPositionsPanel
        portfolioId={portfolioId}
        onImported={(count) => setSnackbar(`Uploaded ${count} position(s) — replaced the previous list`)}
        onAdded={() => setSnackbar("Position added")}
      />

      <PositionsList positions={positions} />

      {activeTemplate && !curveRunId && (
        <Alert
          severity="warning"
          action={
            <Button color="inherit" size="small" onClick={() => router.push("/economic/templates")}>
              Go run it
            </Button>
          }
        >
          &quot;{activeTemplate.name}&quot; hasn&apos;t been run yet — running the portfolio reads the active
          template's own curve run, not a fresh one, so run it first.
        </Alert>
      )}

      <RunPanel
        onRun={() => {
          // Opened *before* the request resolves, not in `onSuccess` -- the run is
          // still one synchronous HTTP call (see `services/run_service.py`'s module
          // docstring), so waiting for `onSuccess` meant the dialog only ever
          // flashed open right as the run had already finished, with no feedback at
          // all during the actual (potentially tens-of-seconds) wait. Clear any
          // previous job/run id first so `RunProgressDialog`'s poll doesn't briefly
          // show the *last* run's already-"succeeded" state before this one's job
          // id comes back.
          setActiveJobId(undefined);
          setActiveRunId(undefined);
          setRunDialogOpen(true);
          startRun.mutate(
            { curve_run_id: curveRunId },
            {
              onSuccess: (created) => {
                setActiveJobId(created.job_id);
                setActiveRunId(created.run_id);
              },
              onError: (err) => {
                setRunDialogOpen(false);
                setSnackbar(`Couldn't start the run: ${(err as Error).message}`);
              },
            },
          );
        }}
        disabled={positions.length === 0 || startRun.isPending || !curveRunId}
      />

      <RunProgressDialog
        open={runDialogOpen}
        jobId={activeJobId}
        fallbackTotal={positions.length}
        onClose={() => setRunDialogOpen(false)}
        onComplete={() => {
          setRunDialogOpen(false);
          router.push(`/assets/results?run_id=${activeRunId}`);
        }}
      />

      <Snackbar open={Boolean(snackbar)} autoHideDuration={3000} onClose={() => setSnackbar(null)} message={snackbar} />
    </Stack>
  );
}
