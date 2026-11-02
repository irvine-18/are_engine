import { Button, Chip, Paper, Stack, Typography } from "@mui/material";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";

import { fmtDate } from "@/lib/format";
import type { JobStatus } from "@/lib/api/types";

const STATUS_COLOR: Record<JobStatus, "success" | "error" | "info" | "default"> = {
  succeeded: "success",
  failed: "error",
  running: "info",
  queued: "default",
  cancelled: "default",
};

export interface RunRow {
  id: string;
  portfolioName: string;
  status: JobStatus;
  createdAt: string;
}

export function RunCard({ run, onViewResults }: { run: RunRow; onViewResults: () => void }) {
  return (
    <Paper sx={{ p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2} flexWrap="wrap" sx={{ gap: 1.5 }}>
        <Stack spacing={0.75} sx={{ minWidth: 0 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography variant="subtitle2">{run.portfolioName}</Typography>
            <Chip size="small" label={run.status} color={STATUS_COLOR[run.status] ?? "default"} />
          </Stack>
          <Typography variant="caption" color="text.secondary">
            Run {run.id} · created {fmtDate(run.createdAt)}
          </Typography>
        </Stack>

        <Stack direction="row" spacing={1} alignItems="center" sx={{ flexShrink: 0 }}>
          <Button size="small" variant="contained" startIcon={<VisibilityOutlinedIcon fontSize="small" />} onClick={onViewResults}>
            View results
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}
