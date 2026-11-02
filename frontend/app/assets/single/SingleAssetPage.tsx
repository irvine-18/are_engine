"use client";

import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Grid, Snackbar, Stack } from "@mui/material";
import { useRouter } from "next/navigation";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageLoadingOverlay } from "@/components/feedback/PageLoadingOverlay";
import { TemplatePicker } from "@/components/economicTemplates/TemplatePicker";
import { TemplateCoverageAlert } from "@/components/economicTemplates/TemplateCoverageAlert";
import { AssetFormPanel } from "./components/AssetFormPanel";
import { AssetResultPanel } from "./components/AssetResultPanel";
import { AddToPortfolioDialog } from "./components/AddToPortfolioDialog";
import { DEFAULT_FORM, type FormState } from "./utils/assetFormConstants";
import { getModellingClassFlags } from "./utils/modellingClassFlags";
import { buildAssetInput } from "./utils/buildAssetInput";
import { validateAssetForm } from "./utils/validateAssetForm";
import { buildPositionCreate } from "@/app/assets/portfolio/utils/buildPositionCreate";
import { formFromAssetInput } from "./utils/formFromAssetInput";
import { useEconomicTemplates } from "@/stores/economicTemplates";
import { useAddPosition, useCalculateAsset, usePortfolioList, useSampleAssets } from "@/lib/api/hooks";
import { toPortfolioSummary } from "@/lib/api/portfolioAdapters";
import { checkTemplateCoverage } from "@/lib/templateValidation";
import { DEFAULT_CURRENCY, defaultValuationDate } from "@/lib/economicTemplates";
import type { SampleAsset } from "@/lib/api/types";

export function SingleAssetPage() {
  const router = useRouter();
  const [form, setForm] = useState(DEFAULT_FORM);
  const [addToPortfolioOpen, setAddToPortfolioOpen] = useState(false);
  const [targetPortfolio, setTargetPortfolio] = useState("");
  const [snackbar, setSnackbar] = useState<string | null>(null);

  // Snapshot of `form` as it was the last time Calculate succeeded. While `form`
  // still matches it, the showing result is current; once they diverge (any field
  // edited, or a different sample loaded), the result is stale -- see `isDirty`
  // below and `AssetResultPanel`'s `dimmed` prop.
  const [lastCalculatedForm, setLastCalculatedForm] = useState<FormState | null>(null);
  const [dirtyDialogOpen, setDirtyDialogOpen] = useState(false);

  const calculateAsset = useCalculateAsset();
  const { data: samples, isLoading: isLoadingSamples } = useSampleAssets();
  const { activeTemplate, isLoading: isLoadingTemplates } = useEconomicTemplates();
  const valuationDate = activeTemplate?.valuationDate ?? defaultValuationDate();
  const currency = activeTemplate?.currency ?? DEFAULT_CURRENCY;
  const { data: portfolioRows, isLoading: isLoadingPortfolios } = usePortfolioList();
  const portfolios = (portfolioRows ?? []).map(toPortfolioSummary);
  const addPositionToPortfolio = useAddPosition(targetPortfolio || undefined);

  const flags = useMemo(() => getModellingClassFlags(form), [form]);
  const errors = useMemo(() => validateAssetForm(form, flags), [form, flags]);

  const isDirty = lastCalculatedForm !== null && JSON.stringify(form) !== JSON.stringify(lastCalculatedForm);

  // Ask once per "dirty" stretch, right when it starts -- not on every keystroke
  // while the dialog is already dismissed and the result stays greyed out.
  useEffect(() => {
    if (isDirty) setDirtyDialogOpen(true);
  }, [isDirty]);

  const coverageIssues = useMemo(
    () =>
      checkTemplateCoverage(activeTemplate, [
        { positionId: "PREVIEW", modellingClass: form.modellingClass, rating: flags.isRated ? form.rating : null },
      ]),
    [activeTemplate, form.modellingClass, form.rating, flags.isRated],
  );

  const asset = useMemo(() => buildAssetInput(form, currency, flags), [form, currency, flags]);

  // Prices against the active template's own last run (`curveRunId` is just the
  // template's own id -- see `backend/src/api/economic_data.py::run_ede_template`,
  // which persists the same `{result, asset_rates_table}` shape `/curves/run` does,
  // under the template's id instead of a fresh random one). Never re-runs Smith-Wilson
  // here -- that's the Templates page's "Run"/"Re-run" button's job.
  const curveRunId = activeTemplate?.lastRun?.curveRunId ?? null;

  const handleCalculate = () => {
    if (!curveRunId || Object.keys(errors).length > 0) return;
    calculateAsset.mutate(
      {
        valuation_date: valuationDate,
        curve_run_id: curveRunId,
        // Omitted, not a fixed ["Base", "SCR_IR_Up", "SCR_IR_Down"] list -- those were
        // never real scenario names once sourced from a template's own run (SCR_IR_Up/
        // Down are a *shock* of the "Base" scenario there, not their own scenario; see
        // `services/economic_service.py::run_eiopa_published_interest_curves`'s
        // docstring). Leaving this unset makes the backend use every scenario the
        // template's run actually produced (`calc_sensitivities_scr_risk`'s own
        // default), covering the template's real custom scenarios too (DV01, IR+50,
        // INF01, ...), not just three that may not even exist in this run's data.
        asset,
      },
      {
        onSuccess: () => {
          setLastCalculatedForm(form);
          setDirtyDialogOpen(false);
        },
      },
    );
  };

  function handleLoadSample(sample: SampleAsset) {
    setForm(formFromAssetInput(sample.asset));
  }

  function handleDiscardChanges() {
    if (lastCalculatedForm) setForm(lastCalculatedForm);
    setDirtyDialogOpen(false);
  }

  const handleAddToPortfolio = () => {
    const portfolio = portfolios.find((p) => p.id === targetPortfolio);
    addPositionToPortfolio.mutate(
      buildPositionCreate(`Single asset — ${form.modellingClass}`, form, currency, flags),
      {
        onSuccess: () => setSnackbar(`Added to ${portfolio?.name ?? targetPortfolio}`),
        onError: (err) => setSnackbar(`Couldn't add to portfolio: ${(err as Error).message}`),
      },
    );
    setAddToPortfolioOpen(false);
  };

  const result = calculateAsset.data;

  return (
    <Stack spacing={2}>
      <PageHeader
        section="Asset Market Risk"
        title="Single Asset Calculator"
        description="Price one instrument against the active curve set and inspect its SCR breakdown, scenario impacts and cashflows."
        icon={<AccountBalanceIcon fontSize="small" />}
        statusLabel="Live"
      />
      <PageLoadingOverlay loading={isLoadingTemplates || isLoadingSamples || isLoadingPortfolios} label="Single Asset">
        <TemplatePicker />
        <TemplateCoverageAlert issues={coverageIssues} />

        {activeTemplate && !curveRunId && (
          <Alert
            severity="warning"
            action={
              <Button color="inherit" size="small" onClick={() => router.push("/economic/templates")}>
                Go run it
              </Button>
            }
          >
            &quot;{activeTemplate.name}&quot; hasn&apos;t been run yet — calculating reads the active template's own
            curve run, not a fresh one, so run it first.
          </Alert>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12} md={3}>
            <AssetFormPanel
              form={form}
              onChange={setForm}
              flags={flags}
              errors={errors}
              samples={samples ?? []}
              onLoadSample={handleLoadSample}
              onCalculate={handleCalculate}
              canCalculate={Boolean(curveRunId)}
              isCalculating={calculateAsset.isPending}
              calculateError={calculateAsset.isError ? (calculateAsset.error as Error) : null}
            />
          </Grid>

          <Grid item xs={12} md={9}>
            <AssetResultPanel result={result} onAddToPortfolio={() => setAddToPortfolioOpen(true)} dimmed={isDirty} />
          </Grid>
        </Grid>
      </PageLoadingOverlay>

      <AddToPortfolioDialog
        open={addToPortfolioOpen}
        onClose={() => setAddToPortfolioOpen(false)}
        portfolios={portfolios}
        targetPortfolio={targetPortfolio}
        onTargetPortfolioChange={setTargetPortfolio}
        onConfirm={handleAddToPortfolio}
        isSubmitting={addPositionToPortfolio.isPending}
      />

      <Dialog open={dirtyDialogOpen} onClose={() => setDirtyDialogOpen(false)}>
        <DialogTitle>Inputs changed</DialogTitle>
        <DialogContent>
          <DialogContentText>
            You&apos;ve changed the asset inputs since the last calculation, so the results shown are now stale. Run
            Calculate again to price the new inputs, or discard your changes to go back to what was last calculated.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDiscardChanges}>Discard changes</Button>
          <Button variant="contained" onClick={handleCalculate} disabled={!curveRunId || Object.keys(errors).length > 0}>
            Recalculate
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={Boolean(snackbar)} autoHideDuration={4000} onClose={() => setSnackbar(null)} message={snackbar} />
    </Stack>
  );
}
