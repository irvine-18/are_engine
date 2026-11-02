"use client";

import { useState } from "react";
import { Alert, Button, CircularProgress, Divider, LinearProgress, Step, StepLabel, Stepper, Stack, TextField, Typography } from "@mui/material";
import SaveIcon from "@mui/icons-material/Save";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";

import { ScenariosEditor } from "./sections/scenarios/ScenariosEditor";
import { RunContextSection } from "./sections/run-context/RunContextSection";
import { InterestSection } from "./sections/interest/InterestSection";
import { InterestSwapRatesPage } from "./sections/interest/InterestSwapRatesPage";
import { InflationSection } from "./sections/inflation/InflationSection";
import { InflationSwapRatesPage } from "./sections/inflation/InflationSwapRatesPage";
import { EquitySection } from "./sections/equity/EquitySection";
import { CreditSpreadSection } from "./sections/credit-spread/CreditSpreadSection";
import { validateTemplate } from "./utils/validateTemplate";
import type { EconomicDataTemplate } from "@/lib/economicTemplates";
import type { ScenarioDefinition } from "@/lib/scenarios";

const STEPS = ["Sections", "Scenarios"];

export function EconomicTemplateBuilder({
  initial,
  onSave,
  onSaveAndRun,
  onCancel,
  isSavingAndRunning = false,
}: {
  initial: EconomicDataTemplate;
  onSave: (template: EconomicDataTemplate) => void;
  /** Saves the template, then runs it (`POST .../run-ede-template/{id}`) --
   * see `EconomicTemplatesPage`'s `handleSaveAndRun`, which shows a success dialog
   * once the run itself completes. */
  onSaveAndRun: (template: EconomicDataTemplate) => void;
  onCancel: () => void;
  /** True while `onSaveAndRun`'s save+run round trip is in flight -- disables every
   * footer action so the user can't double-submit or navigate away mid-run. */
  isSavingAndRunning?: boolean;
}) {
  const [template, setTemplate] = useState<EconomicDataTemplate>(initial);
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [swapRatesPageOpen, setSwapRatesPageOpen] = useState(false);
  const [inflationSwapRatesPageOpen, setInflationSwapRatesPageOpen] = useState(false);

  function setScenarios(scenarios: ScenarioDefinition[]) {
    setTemplate((t) => ({ ...t, scenarios }));
  }
  function patchInterest(patch: Partial<EconomicDataTemplate["interest"]>) {
    setTemplate((t) => ({ ...t, interest: { ...t.interest, ...patch } }));
  }
  function patchInflation(patch: Partial<EconomicDataTemplate["inflation"]>) {
    setTemplate((t) => ({ ...t, inflation: { ...t.inflation, ...patch } }));
  }
  function patchHicp(patch: Partial<EconomicDataTemplate["hicp"]>) {
    setTemplate((t) => ({ ...t, hicp: { ...t.hicp, ...patch } }));
  }
  function patchEquity(patch: Partial<EconomicDataTemplate["equity"]>) {
    setTemplate((t) => ({ ...t, equity: { ...t.equity, ...patch } }));
  }
  function patchCreditSpread(patch: Partial<EconomicDataTemplate["creditSpread"]>) {
    setTemplate((t) => ({ ...t, creditSpread: { ...t.creditSpread, ...patch } }));
  }

  function handleNext() {
    const validationError = validateTemplate(template);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setStep(1);
  }

  function handleSave() {
    const validationError = validateTemplate(template);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    onSave(template);
  }

  function handleSaveAndRun() {
    const validationError = validateTemplate(template);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    onSaveAndRun(template);
  }

  if (swapRatesPageOpen) {
    return (
      <InterestSwapRatesPage
        valuationDate={template.valuationDate}
        points={template.interest.liquidPoints}
        onChangePoints={(liquidPoints) => patchInterest({ liquidPoints })}
        swParameters={template.interest.swParameters}
        onChangeSwParameters={(swParameters) => patchInterest({ swParameters })}
        scrShocks={template.interest.scrShocks}
        onChangeScrShocks={(scrShocks) => patchInterest({ scrShocks })}
        onDone={() => setSwapRatesPageOpen(false)}
      />
    );
  }

  if (inflationSwapRatesPageOpen) {
    return (
      <InflationSwapRatesPage
        valuationDate={template.valuationDate}
        points={template.inflation.liquidPoints}
        onChangePoints={(liquidPoints) => patchInflation({ liquidPoints })}
        swParameters={template.inflation.swParameters}
        onChangeSwParameters={(swParameters) => patchInflation({ swParameters })}
        onDone={() => setInflationSwapRatesPageOpen(false)}
      />
    );
  }

  return (
    <Stack spacing={2}>
      <Stepper activeStep={step}>
        {STEPS.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <TextField
        label="Template name"
        fullWidth
        value={template.name}
        onChange={(e) => setTemplate({ ...template, name: e.target.value })}
      />

      {step === 0 && (
        <Stack spacing={2}>
          <RunContextSection
            valuationDate={template.valuationDate}
            currency={template.currency}
            projectionHorizonYears={template.projectionHorizonYears}
            onChangeValuationDate={(valuationDate) => setTemplate((t) => ({ ...t, valuationDate }))}
            onChangeCurrency={(currency) => setTemplate((t) => ({ ...t, currency }))}
            onChangeProjectionHorizonYears={(projectionHorizonYears) => setTemplate((t) => ({ ...t, projectionHorizonYears }))}
          />
          <InterestSection interest={template.interest} onPatch={patchInterest} onOpenSwapRates={() => setSwapRatesPageOpen(true)} />
          <InflationSection
            inflation={template.inflation}
            onPatchInflation={patchInflation}
            onOpenSwapRates={() => setInflationSwapRatesPageOpen(true)}
            hicp={template.hicp}
            onPatchHicp={patchHicp}
          />
          <EquitySection equity={template.equity} onPatch={patchEquity} />
          <CreditSpreadSection creditSpread={template.creditSpread} onPatch={patchCreditSpread} />
        </Stack>
      )}

      {step === 1 && (
        <Stack spacing={2}>
          <Alert severity="info">
            Each scenario carries its own "apply to" setting — liquid part then re-extrapolate (ex-ante) or after
            extrapolation (post-ante). Every active scenario below applies automatically to any included section
            that uses scenarios.
          </Alert>
          <ScenariosEditor
            scenarios={template.scenarios}
            onChange={setScenarios}
            interestUsesEiopaPublished={template.interest.sourceMode === "eiopa_published"}
          />
        </Stack>
      )}

      {error && <Alert severity="error">{error}</Alert>}

      {isSavingAndRunning && (
        <Stack spacing={0.5}>
          {/* Indeterminate -- a template run is one ~16s+ blocking HTTP call with no
          step-level progress to report, so this is honestly "something is
          happening," not a real percentage. */}
          <LinearProgress sx={{ borderRadius: 1 }} />
          <Typography variant="caption" color="text.secondary">
            Saving and running the economic data engine — this might take a minute or two.
          </Typography>
        </Stack>
      )}

      <Divider />
      <Stack direction="row" spacing={1} justifyContent="flex-end">
        <Button variant="outlined" onClick={onCancel} disabled={isSavingAndRunning}>
          Cancel
        </Button>
        {step === 1 && (
          <Button variant="outlined" startIcon={<ArrowBackIcon />} onClick={() => setStep(0)} disabled={isSavingAndRunning}>
            Back
          </Button>
        )}
        {step === 0 ? (
          <Button variant="contained" endIcon={<ArrowForwardIcon />} onClick={handleNext}>
            Next: Scenarios
          </Button>
        ) : (
          <>
            <Button variant="outlined" startIcon={<SaveIcon />} onClick={handleSave} disabled={isSavingAndRunning}>
              Save template
            </Button>
            <Button
              variant="contained"
              startIcon={isSavingAndRunning ? <CircularProgress size={16} color="inherit" /> : <PlayArrowIcon />}
              onClick={handleSaveAndRun}
              disabled={isSavingAndRunning}
            >
              {isSavingAndRunning ? "Saving & running…" : "Save & Run"}
            </Button>
          </>
        )}
      </Stack>
    </Stack>
  );
}
