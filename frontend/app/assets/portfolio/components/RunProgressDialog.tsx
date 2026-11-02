import { useEffect } from "react";
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, LinearProgress, Stack, Typography } from "@mui/material";

import { useJob } from "@/lib/api/hooks";

interface RunProgressDialogProps {
  open: boolean;
  jobId: string | undefined;
  /** Position count known immediately on click, before `jobId` exists (the run is
   * still a single synchronous HTTP call -- see `services/run_service.py`'s module
   * docstring -- so there's no real job to poll until it's already finished). Shown
   * as "0 / N" during that wait instead of a blank "0 / 0". */
  fallbackTotal?: number;
  onClose: () => void;
  onComplete: () => void;
}

export function RunProgressDialog({ open, jobId, fallbackTotal, onClose, onComplete }: RunProgressDialogProps) {
  const { data: job } = useJob(jobId, { enabled: open });
  const done = job?.status === "succeeded" || job?.status === "failed" || job?.status === "cancelled";

  useEffect(() => {
    if (open && job?.status === "succeeded") onComplete();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, job?.status]);

  const total = job?.positions_total ?? fallbackTotal ?? 0;
  const positionsDone = job?.positions_done ?? 0;
  const progress = job ? (total > 0 ? (positionsDone / total) * 100 : 0) : 0;

  return (
    <Dialog open={open} onClose={done ? onClose : undefined} maxWidth="xs" fullWidth>
      <DialogTitle>Running portfolio SCR</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <LinearProgress variant={job ? "determinate" : "indeterminate"} value={progress} />
          {!job && (
            <Typography variant="caption" color="text.secondary">
              Pricing {total > 0 ? `${total} position(s)` : "every position"} — this may take a moment.
            </Typography>
          )}
          <Stack direction="row" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">
              Positions processed
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {positionsDone} / {total}
            </Typography>
          </Stack>
          <Stack direction="row" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">
              Errors so far
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {job?.error_count ?? 0}
            </Typography>
          </Stack>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={!done}>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
}
