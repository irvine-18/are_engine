"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  Grid,
  IconButton,
  MenuItem,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import RestartAltIcon from "@mui/icons-material/RestartAlt";

import {
  formatSigned,
  type InflationShock,
  type InterestShock,
  type ScenarioApplyTo,
  type ScenarioCategory,
  type ScenarioDefinition,
  type TenorShock,
} from "@/lib/scenarios";

type InterestType = "none" | "parallel_bps" | "custom_per_tenor";
type InflationType = "none" | "parallel_bps" | "custom_per_tenor";

function ApplyToRadioGroup({
  value,
  onChange,
  disableExAnte,
  warning,
}: {
  value: ScenarioApplyTo;
  onChange: (value: ScenarioApplyTo) => void;
  disableExAnte?: boolean;
  warning?: string;
}) {
  return (
    <Stack spacing={0.5}>
      <Typography variant="caption" color="text.secondary">
        Apply to
      </Typography>
      <RadioGroup row value={value} onChange={(e) => onChange(e.target.value as ScenarioApplyTo)}>
        <FormControlLabel value="liquid_then_re_extrapolate" control={<Radio size="small" />} label="Ex-Ante" disabled={disableExAnte} />
        <FormControlLabel value="after_extrapolation" control={<Radio size="small" />} label="Post-Ante" />
      </RadioGroup>
      {disableExAnte && warning && (
        <Alert severity="warning" sx={{ mt: 0.5 }}>
          {warning}
        </Alert>
      )}
    </Stack>
  );
}

function TenorShockGrid({ rows, onChange }: { rows: TenorShock[]; onChange: (rows: TenorShock[]) => void }) {
  return (
    <Stack spacing={1}>
      <Stack direction="row" spacing={1}>
        <Typography variant="caption" color="text.secondary" sx={{ flex: 1 }}>
          Maturity (years)
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ flex: 1 }}>
          Shift (bp)
        </Typography>
        <Box sx={{ width: 32 }} />
      </Stack>
      {rows.map((row, idx) => (
        <Stack direction="row" spacing={1} key={idx} alignItems="center">
          <TextField
            size="small"
            type="number"
            value={row.maturityYears}
            onChange={(e) => onChange(rows.map((r, i) => (i === idx ? { ...r, maturityYears: Number(e.target.value) } : r)))}
            sx={{ flex: 1 }}
          />
          <TextField
            size="small"
            type="number"
            value={row.shiftBps}
            onChange={(e) => onChange(rows.map((r, i) => (i === idx ? { ...r, shiftBps: Number(e.target.value) } : r)))}
            sx={{ flex: 1 }}
          />
          <IconButton size="small" disabled={rows.length <= 1} onClick={() => onChange(rows.filter((_, i) => i !== idx))}>
            <DeleteOutlineIcon fontSize="small" />
          </IconButton>
        </Stack>
      ))}
      <Button size="small" variant="outlined" startIcon={<AddIcon />} sx={{ alignSelf: "flex-start" }} onClick={() => onChange([...rows, { maturityYears: rows.at(-1)?.maturityYears ?? 1, shiftBps: 0 }])}>
        Add tenor
      </Button>
    </Stack>
  );
}

function suggestName(values: {
  interestType: InterestType;
  interestBps: number;
  inflationType: InflationType;
  inflationBps: number;
  equityPct: number | null;
}) {
  const parts: string[] = [];
  if (values.interestType === "parallel_bps") parts.push(`IR${formatSigned(values.interestBps)}`);
  else if (values.interestType === "custom_per_tenor") parts.push("IR_CUSTOM");

  if (values.inflationType === "parallel_bps") parts.push(`INF${formatSigned(values.inflationBps)}`);
  else if (values.inflationType === "custom_per_tenor") parts.push("INF_CUSTOM");

  if (values.equityPct !== null) parts.push(`EQ${formatSigned(values.equityPct)}%`);

  return parts.length ? parts.join("_") : "Scenario";
}

function getCategory(interestShock: InterestShock, inflationShock: InflationShock, equityPct: number | null): ScenarioCategory {
  const hasInterest = interestShock.type !== "none";
  const hasInflation = inflationShock.type !== "none";
  if (hasInterest && hasInflation) return "Combined";
  if (hasInterest) return "Interest rate";
  if (hasInflation) return "Inflation";
  if (equityPct !== null) return "Equity";
  return "Combined";
}

function describeApplyTo(applyTo: ScenarioApplyTo) {
  return applyTo === "liquid_then_re_extrapolate" ? "pre-ante (liquid curve, then re-extrapolate)" : "post-ante (after extrapolation)";
}

function describeScenario(values: {
  interestType: InterestType;
  interestBps: number;
  interestRows: TenorShock[];
  interestApplyTo: ScenarioApplyTo;
  inflationType: InflationType;
  inflationBps: number;
  inflationRows: TenorShock[];
  inflationApplyTo: ScenarioApplyTo;
  equityPct: number | null;
}) {
  const parts: string[] = [];
  if (values.interestType === "parallel_bps") parts.push(`interest ${formatSigned(values.interestBps)} bp, ${describeApplyTo(values.interestApplyTo)}`);
  else if (values.interestType === "custom_per_tenor")
    parts.push(`interest custom curve at ${values.interestRows.length} tenors, ${describeApplyTo(values.interestApplyTo)}`);

  if (values.inflationType === "parallel_bps") parts.push(`inflation ${formatSigned(values.inflationBps)} bp, ${describeApplyTo(values.inflationApplyTo)}`);
  else if (values.inflationType === "custom_per_tenor")
    parts.push(`inflation custom curve at ${values.inflationRows.length} tenors, ${describeApplyTo(values.inflationApplyTo)}`);

  if (values.equityPct !== null) parts.push(`equity ${formatSigned(values.equityPct)}%`);

  return parts.length ? `${parts.join(" · ")}.` : "No shocks defined.";
}

export function ScenarioFormDialog({
  open,
  onOpenChange,
  onCreate,
  interestUsesEiopaPublished,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreate: (scenario: ScenarioDefinition) => void;
  /** EIOPA's published curve has no liquid part to re-run Smith-Wilson against, so only a
   * direct post-ante shift to the published curve is possible -- ex-ante shocks (which
   * require re-extrapolating the liquid part) don't apply. */
  interestUsesEiopaPublished: boolean;
}) {
  const [nameEdited, setNameEdited] = useState(false);
  const [name, setName] = useState("IR+50");
  const [interestType, setInterestType] = useState<InterestType>("parallel_bps");
  const [interestBps, setInterestBps] = useState(50);
  const [interestRows, setInterestRows] = useState<TenorShock[]>([
    { maturityYears: 1, shiftBps: 25 },
    { maturityYears: 10, shiftBps: 50 },
    { maturityYears: 30, shiftBps: 75 },
  ]);
  const [interestApplyTo, setInterestApplyTo] = useState<ScenarioApplyTo>("liquid_then_re_extrapolate");
  const [inflationType, setInflationType] = useState<InflationType>("none");
  const [inflationBps, setInflationBps] = useState(50);
  const [inflationRows, setInflationRows] = useState<TenorShock[]>([
    { maturityYears: 1, shiftBps: 25 },
    { maturityYears: 10, shiftBps: 50 },
  ]);
  const [inflationApplyTo, setInflationApplyTo] = useState<ScenarioApplyTo>("liquid_then_re_extrapolate");
  const [equityPct, setEquityPct] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const suggested = useMemo(
    () => suggestName({ interestType, interestBps, inflationType, inflationBps, equityPct }),
    [interestType, interestBps, inflationType, inflationBps, equityPct],
  );

  useEffect(() => {
    if (!nameEdited) setName(suggested);
  }, [nameEdited, suggested]);

  useEffect(() => {
    if (interestUsesEiopaPublished) setInterestApplyTo("after_extrapolation");
  }, [interestUsesEiopaPublished]);

  function reset() {
    setNameEdited(false);
    setName("IR+50");
    setInterestType("parallel_bps");
    setInterestBps(50);
    setInterestApplyTo(interestUsesEiopaPublished ? "after_extrapolation" : "liquid_then_re_extrapolate");
    setInflationType("none");
    setInflationBps(50);
    setInflationApplyTo("liquid_then_re_extrapolate");
    setEquityPct(null);
    setError(null);
  }

  function handleClose() {
    onOpenChange(false);
    reset();
  }

  function handleSubmit() {
    if (interestType === "none" && inflationType === "none" && equityPct === null) {
      setError("Add at least one interest, inflation, or equity shock.");
      return;
    }
    if (interestType === "custom_per_tenor" && interestRows.length === 0) {
      setError("Add at least one interest-rate tenor.");
      return;
    }
    if (inflationType === "custom_per_tenor" && inflationRows.length === 0) {
      setError("Add at least one inflation tenor.");
      return;
    }

    const interestShock: InterestShock =
      interestType === "parallel_bps"
        ? { type: "parallel_bps", shiftBps: interestBps }
        : interestType === "custom_per_tenor"
          ? { type: "custom_per_tenor", rows: interestRows }
          : { type: "none" };
    const inflationShock: InflationShock =
      inflationType === "parallel_bps"
        ? { type: "parallel_bps", shiftBps: inflationBps }
        : inflationType === "custom_per_tenor"
          ? { type: "custom_per_tenor", rows: inflationRows }
          : { type: "none" };

    const scenario: ScenarioDefinition = {
      id: `user-${typeof crypto !== "undefined" ? crypto.randomUUID() : `${Date.now()}`}`,
      name: name.trim() || suggested,
      category: getCategory(interestShock, inflationShock, equityPct),
      description: describeScenario({
        interestType,
        interestBps,
        interestRows,
        interestApplyTo,
        inflationType,
        inflationBps,
        inflationRows,
        inflationApplyTo,
        equityPct,
      }),
      active: true,
      builtIn: false,
      interestShock,
      interestApplyTo,
      inflationShock,
      inflationApplyTo,
      equityShockPercent: equityPct,
    };

    onCreate(scenario);
    reset();
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>New scenario</DialogTitle>
      <DialogContent>
        <Stack spacing={3}>
          <Typography variant="body2" color="text.secondary">
            Define interest, inflation, and optional equity shocks. The engine currently applies flat parallel basis-point
            shocks; per-tenor shifts are previewed here but not yet applied in a run.
          </Typography>

          <Stack direction="row" spacing={1} alignItems="flex-end">
            <TextField
              label="Name"
              size="small"
              fullWidth
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setNameEdited(true);
              }}
            />
            <Button
              size="small"
              startIcon={<RestartAltIcon />}
              onClick={() => {
                setNameEdited(false);
                setName(suggested);
              }}
            >
              Use suggestion
            </Button>
          </Stack>

          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Stack spacing={2} sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 2, height: "100%" }}>
                <Typography variant="subtitle2">Interest</Typography>
                <TextField select size="small" label="Shock type" value={interestType} onChange={(e) => setInterestType(e.target.value as InterestType)}>
                  <MenuItem value="none">None</MenuItem>
                  <MenuItem value="parallel_bps">Parallel shift (bp)</MenuItem>
                  <MenuItem value="custom_per_tenor">Custom per tenor</MenuItem>
                </TextField>
                {interestType === "parallel_bps" && (
                  <TextField size="small" type="number" label="Parallel shift (bp)" value={interestBps} onChange={(e) => setInterestBps(Number(e.target.value))} />
                )}
                {interestType === "custom_per_tenor" && <TenorShockGrid rows={interestRows} onChange={setInterestRows} />}
                {interestType !== "none" && (
                  <ApplyToRadioGroup
                    value={interestApplyTo}
                    onChange={setInterestApplyTo}
                    disableExAnte={interestUsesEiopaPublished}
                    warning="Interest uses the EIOPA RFR publication, which has no liquid part to re-extrapolate -- only Post-Ante (a direct shift to the published curve) applies."
                  />
                )}
              </Stack>
            </Grid>

            <Grid item xs={12} md={4}>
              <Stack spacing={2} sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 2, height: "100%" }}>
                <Typography variant="subtitle2">Inflation</Typography>
                <TextField select size="small" label="Shock type" value={inflationType} onChange={(e) => setInflationType(e.target.value as InflationType)}>
                  <MenuItem value="none">None</MenuItem>
                  <MenuItem value="parallel_bps">Parallel shift (bp)</MenuItem>
                  <MenuItem value="custom_per_tenor">Custom per tenor</MenuItem>
                </TextField>
                {inflationType === "parallel_bps" && (
                  <TextField size="small" type="number" label="Parallel shift (bp)" value={inflationBps} onChange={(e) => setInflationBps(Number(e.target.value))} />
                )}
                {inflationType === "custom_per_tenor" && <TenorShockGrid rows={inflationRows} onChange={setInflationRows} />}
                {inflationType !== "none" && <ApplyToRadioGroup value={inflationApplyTo} onChange={setInflationApplyTo} />}
              </Stack>
            </Grid>

            <Grid item xs={12} md={4}>
              <Stack spacing={2} sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 2, height: "100%" }}>
                <Typography variant="subtitle2">Equity</Typography>
                <TextField
                  size="small"
                  type="number"
                  label="Equity shock (%)"
                  placeholder="Optional"
                  value={equityPct ?? ""}
                  onChange={(e) => setEquityPct(e.target.value === "" ? null : Number(e.target.value))}
                />
              </Stack>
            </Grid>
          </Grid>

          {error && <Alert severity="error">{error}</Alert>}
        </Stack>
      </DialogContent>
      <Divider />
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button variant="outlined" onClick={handleClose}>
          Cancel
        </Button>
        <Button variant="contained" onClick={handleSubmit}>
          Add scenario
        </Button>
      </DialogActions>
    </Dialog>
  );
}
