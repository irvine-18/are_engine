"use client";

import { useMemo, useState } from "react";
import { Button, Divider, Grid, Step, StepLabel, Stepper, Stack, TextField, Typography } from "@mui/material";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import dayjs from "dayjs";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import CheckIcon from "@mui/icons-material/Check";
import EventIcon from "@mui/icons-material/Event";

import { ManualGrid } from "../../components/ManualGrid";
import { UploadTab } from "../../components/UploadTab";
import { getEiopaInflationSwParameters } from "../../utils/eiopaInflationSwParameters";
import { defaultInflationLiquidPoints, type InflationSwParameters } from "@/lib/economicTemplates";
import type { LiquidRatePoint } from "@/lib/api/types";

const STEPS = ["Enter Swap Rates", "SW-Parameters"];

export function InflationSwapRatesPage({
  valuationDate,
  points,
  onChangePoints,
  swParameters,
  onChangeSwParameters,
  onDone,
}: {
  valuationDate: string;
  points: LiquidRatePoint[];
  onChangePoints: (points: LiquidRatePoint[]) => void;
  swParameters: InflationSwParameters;
  onChangeSwParameters: (p: InflationSwParameters) => void;
  onDone: () => void;
}) {
  const [step, setStep] = useState(0);
  const requiredPoints = useMemo(() => defaultInflationLiquidPoints(), []);

  return (
    <Stack spacing={2}>
      <Button size="small" startIcon={<ArrowBackIcon />} onClick={onDone} sx={{ alignSelf: "flex-start" }}>
        Back to template
      </Button>

      <Typography variant="h6">Enter inflation swap rates</Typography>

      <Stepper activeStep={step}>
        {STEPS.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {step === 0 && (
        <Stack spacing={3}>
          <ManualGrid
            points={points}
            onChange={onChangePoints}
            rateLabel="ZC inflation swap rate (%)"
            height={480}
            requiredPoints={requiredPoints}
          />
          <Divider>OR</Divider>
          <Stack spacing={1}>
            <Typography variant="subtitle2">Upload swap rates</Typography>
            <UploadTab onParsed={onChangePoints} />
          </Stack>
        </Stack>
      )}

      {step === 1 && (
        <SwParametersStep valuationDate={valuationDate} swParameters={swParameters} onChange={onChangeSwParameters} />
      )}

      <Divider />
      <Stack direction="row" spacing={1} justifyContent="flex-end">
        {step > 0 && (
          <Button variant="outlined" startIcon={<ArrowBackIcon />} onClick={() => setStep((s) => s - 1)}>
            Back
          </Button>
        )}
        {step < STEPS.length - 1 ? (
          <Button variant="contained" endIcon={<ArrowForwardIcon />} onClick={() => setStep((s) => s + 1)}>
            Next: {STEPS[step + 1]}
          </Button>
        ) : (
          <Button variant="contained" startIcon={<CheckIcon />} onClick={onDone}>
            Done
          </Button>
        )}
      </Stack>
    </Stack>
  );
}

function SwParametersStep({
  valuationDate,
  swParameters,
  onChange,
}: {
  valuationDate: string;
  swParameters: InflationSwParameters;
  onChange: (p: InflationSwParameters) => void;
}) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [eiopaMonth, setEiopaMonth] = useState(valuationDate.slice(0, 7));

  return (
    <Stack spacing={2}>
      <Typography variant="body2" color="text.secondary">
        Calibrates the Smith-Wilson extrapolation used for the Cost Inflation curve — the curve asset pricing
        actually reads — not the market-implied inflation curve above, which is taken straight from the swap rates
        with no extrapolation.
      </Typography>

      <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap" sx={{ rowGap: 1 }}>
        <Button size="small" startIcon={<EventIcon fontSize="small" />} onClick={() => setPickerOpen((v) => !v)}>
          Use EIOPA parameters
        </Button>
        {pickerOpen && (
          <DatePicker
            label="Publication month"
            views={["year", "month"]}
            openTo="month"
            value={dayjs(`${eiopaMonth}-01`)}
            onChange={(value) => {
              if (!value) return;
              const month = value.format("YYYY-MM");
              setEiopaMonth(month);
              onChange(getEiopaInflationSwParameters(month));
            }}
            slotProps={{ textField: { size: "small", sx: { maxWidth: 220 } } }}
          />
        )}
      </Stack>

      <Grid container spacing={2}>
        <Grid item xs={12} sm={4}>
          <TextField
            fullWidth
            label="UFR (%)"
            type="number"
            value={swParameters.ufr * 100}
            onChange={(e) => onChange({ ...swParameters, ufr: Number(e.target.value) / 100 })}
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <TextField
            fullWidth
            label="CRA (bp)"
            type="number"
            value={swParameters.cra * 10000}
            onChange={(e) => onChange({ ...swParameters, cra: Number(e.target.value) / 10000 })}
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <TextField
            fullWidth
            label="Convergence point (years)"
            type="number"
            value={swParameters.convergenceYears}
            onChange={(e) => onChange({ ...swParameters, convergenceYears: Number(e.target.value) })}
          />
        </Grid>
      </Grid>
    </Stack>
  );
}
