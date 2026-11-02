"use client";

import { Box, Grid, MenuItem, Paper, Stack, TextField, Typography } from "@mui/material";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";

const CURRENCIES = ["EUR", "USD", "GBP", "CHF"];

/** "0. Run Context" -- the template's own valuation date, currency and projection
 * horizon, entered before every other section since Interest/Inflation/Equity all
 * key off the valuation date (EIOPA publication months, HICP observation, etc.).
 * Unlike the other numbered sections there's no "included" toggle: a template
 * always has exactly one valuation date, currency and horizon, never optional.
 * Replaces the old global "Run Context" header bar (`stores/runContext.ts`,
 * removed) -- every page that used to read a shared valuation date/currency now
 * reads it from the active template instead. */
export function RunContextSection({
  valuationDate,
  currency,
  projectionHorizonYears,
  onChangeValuationDate,
  onChangeCurrency,
  onChangeProjectionHorizonYears,
}: {
  valuationDate: string;
  currency: string;
  projectionHorizonYears: number;
  onChangeValuationDate: (valuationDate: string) => void;
  onChangeCurrency: (currency: string) => void;
  onChangeProjectionHorizonYears: (projectionHorizonYears: number) => void;
}) {
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack spacing={2}>
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Box sx={{ display: "flex", color: "primary.main" }}>
            <CalendarMonthIcon />
          </Box>
          <Typography fontWeight={600}>0. Run Context</Typography>
        </Stack>

        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Valuation date"
              type="date"
              value={valuationDate}
              onChange={(e) => onChangeValuationDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField fullWidth select label="Currency" value={currency} onChange={(e) => onChangeCurrency(e.target.value)}>
              {CURRENCIES.map((c) => (
                <MenuItem key={c} value={c}>
                  {c}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={4} sx={{ pb: 1 }}>
            <TextField
              fullWidth
              label="Projection horizon (years)"
              type="number"
              value={projectionHorizonYears}
              onChange={(e) => onChangeProjectionHorizonYears(Number(e.target.value))}
              helperText="The real curve engine always projects 120 years; this drives the illustrative fallbacks shown before a run."
            />
          </Grid>
        </Grid>
      </Stack>
    </Paper>
  );
}
