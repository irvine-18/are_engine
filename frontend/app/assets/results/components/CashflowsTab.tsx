import { Alert, AlertTitle, Typography } from "@mui/material";

export function CashflowsTab() {
  return (
    <Alert severity="info">
      <AlertTitle>Coming soon</AlertTitle>
      <Typography variant="body2">Cashflow projections for portfolio runs aren't available yet.</Typography>
    </Alert>
  );
}
