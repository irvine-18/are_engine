import { Alert, Paper } from "@mui/material";

export type InflationIndexName = "HICPxT" | "HICP";

export function InflationIndexBanner() {
  return (
    <Paper sx={{ p: 2 }}>
      <Alert severity="info">
        The market-implied curve is linearly interpolated from the active template's Inflation liquid points.
        Scenarios selected for Inflation in that template are overlaid here.
      </Alert>
    </Paper>
  );
}
