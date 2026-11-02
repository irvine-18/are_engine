import { Alert, Button, Chip, FormControlLabel, LinearProgress, Paper, Stack, Switch, Typography } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import ContentCopyOutlinedIcon from "@mui/icons-material/ContentCopyOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import ReplayIcon from "@mui/icons-material/Replay";

import { sectionsIncluded, type EconomicDataTemplate } from "@/lib/economicTemplates";
import { fmtDate } from "@/lib/format";

export function TemplateCard({
  template,
  onUse,
  onView,
  onEdit,
  onDuplicate,
  onDelete,
  onRun,
  isRunning,
}: {
  template: EconomicDataTemplate;
  onUse: (checked: boolean) => void;
  onView: () => void;
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  /** Runs the real economic-data engine for this template -- see
   * /economic/curves and /economic/inflation, which just display whatever this
   * produced (they don't run anything themselves). */
  onRun: () => void;
  isRunning: boolean;
}) {
  // `template.lastRun` is the small Cosmos-safe summary already returned by
  // `GET /economic-data/get-templates` (see schemas/economic_data.py::TemplateLastRun) --
  // no need for a per-card `useTemplateRun` call (that fetches the full Blob-backed
  // curve result) just to know whether a run exists.
  const hasRun = Boolean(template.lastRun);

  return (
    <Paper sx={{ p: 2 }}>
      {isRunning && (
        <Stack spacing={0.5} sx={{ mb: 1.5 }}>
          {/* Indeterminate -- a template run is one ~16s+ blocking HTTP call with no
          step-level progress to report (see EconomicDataPage's "last run" handling),
          so this is honestly "something is happening," not a real percentage. */}
          <LinearProgress sx={{ borderRadius: 1 }} />
          <Typography variant="caption" color="text.secondary">
            Running the economic data engine — this might take a minute or two.
          </Typography>
        </Stack>
      )}
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2} flexWrap="wrap" sx={{ gap: 1.5 }}>
        <Stack spacing={0.75} sx={{ minWidth: 0 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography variant="subtitle2">{template.name}</Typography>
            {template.isDefault && <Chip size="small" color="success" icon={<CheckCircleIcon />} label="Default" />}
            {template.lastRun && (
              <Chip size="small" color="success" variant="outlined" label={`Last run ${fmtDate(template.lastRun.ranAt)}`} />
            )}
          </Stack>
          <Typography variant="caption" color="text.secondary">
            Valuation date {template.valuationDate} · created {fmtDate(template.createdAt)}
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ rowGap: 1 }}>
            {sectionsIncluded(template).map((s) => (
              <Chip key={s} size="small" variant="outlined" label={s} />
            ))}
          </Stack>
          {template.lastRun?.inflationWarning && (
            <Alert severity="warning" sx={{ maxWidth: 520 }}>
              {template.lastRun.inflationWarning}
            </Alert>
          )}
        </Stack>

        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" sx={{ flexShrink: 0, rowGap: 1 }}>
          <Button
            size="small"
            variant="contained"
            startIcon={hasRun ? <ReplayIcon fontSize="small" /> : <PlayArrowIcon fontSize="small" />}
            onClick={onRun}
            disabled={isRunning}
          >
            {isRunning ? "Running…" : hasRun ? "Re-run" : "Run"}
          </Button>
          <Button size="small" startIcon={<VisibilityOutlinedIcon fontSize="small" />} onClick={onView}>
            View
          </Button>
          <Button size="small" startIcon={<EditOutlinedIcon fontSize="small" />} onClick={onEdit}>
            Edit
          </Button>
          <Button size="small" startIcon={<ContentCopyOutlinedIcon fontSize="small" />} onClick={onDuplicate}>
            Duplicate
          </Button>
          <Button size="small" color="error" startIcon={<DeleteOutlineIcon fontSize="small" />} onClick={onDelete}>
            Delete
          </Button>
          <FormControlLabel
            sx={{ ml: 0.5 }}
            label="Use as default"
            control={<Switch size="small" checked={Boolean(template.isDefault)} onChange={(e) => onUse(e.target.checked)} />}
          />
        </Stack>
      </Stack>
    </Paper>
  );
}
