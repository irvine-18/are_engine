import { Button, Chip, Paper, Stack } from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";

import { fmtDate } from "@/lib/format";
import type { Portfolio, Run, RunSummary } from "@/lib/api/types";

interface RunHeaderProps {
  run: Run;
  summary: RunSummary;
  portfolio: Portfolio | undefined;
  onExport: () => void;
  exporting: boolean;
}

export function RunHeader({ run, summary, portfolio, onExport, exporting }: RunHeaderProps) {
  return (
    <Paper sx={{ p: 2.5 }}>
      <Stack direction={{ xs: "column", lg: "row" }} spacing={2} justifyContent="space-between">
        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ rowGap: 1 }}>
          <Chip variant="outlined" label={`Portfolio: ${portfolio?.name ?? run.portfolio_id}`} />
          <Chip variant="outlined" label={`Run: ${fmtDate(run.created_at)}`} />
          <Chip variant="outlined" label={`Scenarios: ${run.scenarios.length}`} />
          <Chip variant="outlined" label={`Positions: ${summary.positions_total - summary.positions_errored} / ${summary.positions_total}`} />
          <Chip
            label={run.status}
            color={run.status === "succeeded" ? "success" : run.status === "failed" ? "error" : "default"}
          />
        </Stack>
        <Stack direction="row" spacing={1} sx={{ flexShrink: 0 }}>
          <Button variant="outlined" startIcon={<DownloadIcon />} onClick={onExport} disabled={exporting}>
            {exporting ? "Preparing export…" : "Export full results (XLSX)"}
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}
