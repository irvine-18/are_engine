"use client";

import { useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Divider,
  FormControlLabel,
  Grid,
  IconButton,
  MenuItem,
  Paper,
  Step,
  StepLabel,
  Stepper,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import dayjs from "dayjs";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import CheckIcon from "@mui/icons-material/Check";
import EventIcon from "@mui/icons-material/Event";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";

import { ManualGrid } from "../../components/ManualGrid";
import { UploadTab } from "../../components/UploadTab";
import { getEiopaSwParameters } from "../../utils/eiopaSwParameters";
import { getEiopaScrShocks } from "../../utils/eiopaScrShocks";
import { defaultInterestLiquidPoints, type InterestScrShocks, type InterestSwParameters } from "@/lib/economicTemplates";
import type { LiquidRatePoint } from "@/lib/api/types";

const STEPS = ["Enter Swap Rates", "SW-Parameters", "SCR Shocks"];

export function InterestSwapRatesPage({
  valuationDate,
  points,
  onChangePoints,
  swParameters,
  onChangeSwParameters,
  scrShocks,
  onChangeScrShocks,
  onDone,
}: {
  valuationDate: string;
  points: LiquidRatePoint[];
  onChangePoints: (points: LiquidRatePoint[]) => void;
  swParameters: InterestSwParameters;
  onChangeSwParameters: (p: InterestSwParameters) => void;
  scrShocks: InterestScrShocks;
  onChangeScrShocks: (s: InterestScrShocks) => void;
  onDone: () => void;
}) {
  const [step, setStep] = useState(0);
  const requiredPoints = useMemo(() => defaultInterestLiquidPoints(), []);

  return (
    <Stack spacing={2}>
      <Button size="small" startIcon={<ArrowBackIcon />} onClick={onDone} sx={{ alignSelf: "flex-start" }}>
        Back to template
      </Button>

      <Typography variant="h6">Enter interest swap rates</Typography>

      <Stepper activeStep={step}>
        {STEPS.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {step === 0 && (
        <Stack spacing={3}>
          <ManualGrid points={points} onChange={onChangePoints} height={480} requiredPoints={requiredPoints} />
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

      {step === 2 && (
        <ScrShocksStep valuationDate={valuationDate} scrShocks={scrShocks} onChange={onChangeScrShocks} />
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
  swParameters: InterestSwParameters;
  onChange: (p: InterestSwParameters) => void;
}) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [eiopaMonth, setEiopaMonth] = useState(valuationDate.slice(0, 7));

  return (
    <Stack spacing={2}>
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
              onChange({ ...swParameters, ...getEiopaSwParameters(month) });
            }}
            slotProps={{ textField: { size: "small", sx: { maxWidth: 220 } } }}
          />
        )}
      </Stack>

      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField select fullWidth label="Method" value={swParameters.method} disabled>
            <MenuItem value="smith_wilson">Smith-Wilson · EIOPA</MenuItem>
          </TextField>
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Last liquid point (years)"
            type="number"
            value={swParameters.lastLiquidPointYears}
            onChange={(e) => onChange({ ...swParameters, lastLiquidPointYears: Number(e.target.value) })}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="UFR (%)"
            type="number"
            value={swParameters.ufr * 100}
            onChange={(e) => onChange({ ...swParameters, ufr: Number(e.target.value) / 100 })}
            helperText="Use EIOPA's published UFR for the valuation year."
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Convergence point (years)"
            type="number"
            value={swParameters.convergenceYears}
            onChange={(e) => onChange({ ...swParameters, convergenceYears: Number(e.target.value) })}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Convergence tolerance (bp)"
            type="number"
            value={swParameters.convergenceToleranceBp}
            onChange={(e) => onChange({ ...swParameters, convergenceToleranceBp: Number(e.target.value) })}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="CRA (bp)"
            type="number"
            value={swParameters.cra * 10000}
            onChange={(e) => onChange({ ...swParameters, cra: Number(e.target.value) / 10000 })}
          />
        </Grid>
      </Grid>

      <Divider />

      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} sm={6}>
          <FormControlLabel
            control={<Switch checked={swParameters.alphaAutoSolve} onChange={(e) => onChange({ ...swParameters, alphaAutoSolve: e.target.checked })} />}
            label="Auto-solve alpha"
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Manual alpha"
            type="number"
            disabled={swParameters.alphaAutoSolve}
            value={swParameters.alphaManual ?? ""}
            onChange={(e) => onChange({ ...swParameters, alphaManual: e.target.value === "" ? null : Number(e.target.value) })}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Alpha lower bound"
            type="number"
            value={swParameters.alphaLowerBound}
            onChange={(e) => onChange({ ...swParameters, alphaLowerBound: Number(e.target.value) })}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <FormControlLabel
            control={<Switch checked={swParameters.includeVA} onChange={(e) => onChange({ ...swParameters, includeVA: e.target.checked })} />}
            label="Include Volatility Adjustment"
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="VA (bp)"
            type="number"
            disabled={!swParameters.includeVA}
            value={swParameters.va * 10000}
            onChange={(e) => onChange({ ...swParameters, va: Number(e.target.value) / 10000 })}
          />
        </Grid>
      </Grid>
    </Stack>
  );
}

function ScrShocksStep({
  valuationDate,
  scrShocks,
  onChange,
}: {
  valuationDate: string;
  scrShocks: InterestScrShocks;
  onChange: (s: InterestScrShocks) => void;
}) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [eiopaMonth, setEiopaMonth] = useState(valuationDate.slice(0, 7));

  function updateRow(index: number, patch: Partial<InterestScrShocks["table"][number]>) {
    onChange({ ...scrShocks, table: scrShocks.table.map((r, i) => (i === index ? { ...r, ...patch } : r)) });
  }

  return (
    <Stack spacing={2}>
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
              onChange({ ...scrShocks, ...getEiopaScrShocks(month) });
            }}
            slotProps={{ textField: { size: "small", sx: { maxWidth: 220 } } }}
          />
        )}
      </Stack>

      {/* <Grid container spacing={2} maxWidth={620}>
        <Grid item xs={6}>
          <TextField
            select
            fullWidth
            label="Methodology"
            value={scrShocks.methodology}
            onChange={(e) => onChange({ ...scrShocks, methodology: e.target.value as InterestScrShocks["methodology"] })}
          >
            <MenuItem value="standard_formula">Standard formula</MenuItem>
            <MenuItem value="revised_2026">Revised shock method</MenuItem>
            <MenuItem value="custom">Custom</MenuItem>
          </TextField>
        </Grid>
        <Grid item xs={6}>
          <TextField
            fullWidth
            label="DV01/IR01 bump (bp)"
            type="number"
            value={scrShocks.sensitivityBumpBp}
            onChange={(e) => onChange({ ...scrShocks, sensitivityBumpBp: Number(e.target.value) })}
          />
        </Grid>
      </Grid> */}

      <Stack spacing={1.5}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="subtitle2">Shock table</Typography>
          <Button
            size="small"
            startIcon={<AddIcon fontSize="small" />}
            onClick={() => onChange({ ...scrShocks, table: [...scrShocks.table, { maturity_years: 0, up: 0, down: 0 }] })}
          >
            Add maturity
          </Button>
        </Stack>
        <Typography variant="body2" color="text.secondary">
          Maturities should be unique and increasing. Up/down shocks are decimal fractions (0.7 = 70%).
        </Typography>
        <Paper variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Maturity (years)</TableCell>
                <TableCell>Up shock</TableCell>
                <TableCell>Down shock</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {scrShocks.table.map((row, idx) => (
                <TableRow key={idx} hover>
                  <TableCell>
                    <TextField
                      size="small"
                      type="number"
                      value={row.maturity_years}
                      onChange={(e) => updateRow(idx, { maturity_years: Number(e.target.value) })}
                      sx={{ maxWidth: 140 }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="number"
                      value={row.up}
                      onChange={(e) => updateRow(idx, { up: Number(e.target.value) })}
                      sx={{ maxWidth: 120 }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="number"
                      value={row.down}
                      onChange={(e) => updateRow(idx, { down: Number(e.target.value) })}
                      sx={{ maxWidth: 120 }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={() => onChange({ ...scrShocks, table: scrShocks.table.filter((_, i) => i !== idx) })}>
                      <DeleteOutlineIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {scrShocks.table.length === 0 && (
            <Box sx={{ p: 2 }}>
              <Alert severity="info">No shock rows yet. Add maturities above, or leave empty to fall back to the default shock table.</Alert>
            </Box>
          )}
        </Paper>
      </Stack>
    </Stack>
  );
}
