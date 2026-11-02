import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField, Typography } from "@mui/material";

import type { PortfolioSummary } from "@/lib/sampleData/portfolio";

interface AddToPortfolioDialogProps {
  open: boolean;
  onClose: () => void;
  portfolios: PortfolioSummary[];
  targetPortfolio: string;
  onTargetPortfolioChange: (id: string) => void;
  onConfirm: () => void;
  isSubmitting: boolean;
}

export function AddToPortfolioDialog({
  open,
  onClose,
  portfolios,
  targetPortfolio,
  onTargetPortfolioChange,
  onConfirm,
  isSubmitting,
}: AddToPortfolioDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xs"
      fullWidth
      TransitionProps={{ onEnter: () => onTargetPortfolioChange(targetPortfolio || portfolios[0]?.id || "") }}
    >
      <DialogTitle>Add to portfolio</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {portfolios.length === 0 ? (
            <Alert severity="info">No portfolios yet — create one from the Portfolio Construction page first.</Alert>
          ) : (
            <>
              <Typography variant="body2" color="text.secondary">
                This appends the priced instrument to a portfolio&apos;s position list.
              </Typography>
              <TextField select label="Portfolio" value={targetPortfolio} onChange={(e) => onTargetPortfolioChange(e.target.value)}>
                {portfolios.map((p) => (
                  <MenuItem key={p.id} value={p.id}>
                    {p.name}
                  </MenuItem>
                ))}
              </TextField>
            </>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" disabled={!targetPortfolio || isSubmitting} onClick={onConfirm}>
          Add
        </Button>
      </DialogActions>
    </Dialog>
  );
}
