"use client";

import { useMemo, useState } from "react";
import { Alert, Button, Stack, Tab, Tabs } from "@mui/material";
import { usePathname, useRouter } from "next/navigation";
import ShowChartIcon from "@mui/icons-material/ShowChart";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageLoadingOverlay } from "@/components/feedback/PageLoadingOverlay";
import { TemplatePicker } from "@/components/economicTemplates/TemplatePicker";
import { useEconomicTemplates } from "@/stores/economicTemplates";
import { useTemplateRun } from "@/lib/api/hooks";
import { fmtDate } from "@/lib/format";
import { costInflationSeries, observedHicp } from "@/lib/sampleData/inflation";
import { DEFAULT_PROJECTION_HORIZON_YEARS } from "@/lib/economicTemplates";
import type { CurveSet } from "@/lib/api/types";

import { CurveSetControl } from "./components/CurveSetControl";
import { CurveKpiRow } from "./components/CurveKpiRow";
import { CurveRateChart } from "./components/CurveRateChart";
import {
  selectBaseScenario as selectBaseInterestScenario,
  selectCustomInterestScenarios,
  selectDownScenario,
  selectUpScenario,
} from "./utils/curveSelectors";

import { type InflationIndexName } from "../inflation/components/InflationIndexBanner";
import { InflationKpiRow } from "../inflation/components/InflationKpiRow";
import { InflationCurveChart } from "../inflation/components/InflationCurveChart";
import { HicpProjectionChart } from "../inflation/components/HicpProjectionChart";
import {
  selectBaseScenario as selectBaseInflationScenario,
  scenarioCurveToInflationPoints,
} from "../inflation/utils/inflationSelectors";
import {
  buildHicpProjections,
  buildScenarioSeries,
  selectInflationScenarios,
} from "../inflation/utils/inflationScenarios";

type Tab = "curves" | "inflation";

const ROUTES: Record<Tab, string> = {
  curves: "/economic/curves",
  inflation: "/economic/inflation",
};

export function EconomicDataPage() {
  const router = useRouter();
  const pathname = usePathname();
  const tab: Tab = pathname.startsWith("/economic/inflation")
    ? "inflation"
    : "curves";

  const [curveSet, setCurveSet] = useState<CurveSet>("EIOPA_incl_VA");
  const { activeTemplate, isLoading: isLoadingTemplates } = useEconomicTemplates();
  const indexName: InflationIndexName = "HICPxT";
  const { data: run, isLoading: isLoadingRun } = useTemplateRun(
    activeTemplate?.id ?? undefined,
  );

  const curveScenarios = run?.curve_sets[curveSet];
  const kpis = run?.kpis[curveSet] ?? activeTemplate?.lastRun?.kpis[curveSet];
  const baseScenario = useMemo(
    () => selectBaseInterestScenario(curveScenarios),
    [curveScenarios],
  );
  const upScenario = useMemo(
    () => selectUpScenario(curveScenarios),
    [curveScenarios],
  );
  const downScenario = useMemo(
    () => selectDownScenario(curveScenarios),
    [curveScenarios],
  );
  const customScenarios = useMemo(
    () => selectCustomInterestScenarios(activeTemplate),
    [activeTemplate],
  );

  const projectionHorizonYears =
    activeTemplate?.projectionHorizonYears ?? DEFAULT_PROJECTION_HORIZON_YEARS;

  const costInfl = useMemo(
    () =>
      scenarioCurveToInflationPoints(
        selectBaseInflationScenario(run?.cost_inflation),
      ) ?? costInflationSeries(projectionHorizonYears),
    [run, projectionHorizonYears],
  );
  const observed = useMemo(() => observedHicp(24), []);
  const latest = observed[observed.length - 1];

  const inflationScenarios = useMemo(
    () => selectInflationScenarios(activeTemplate),
    [activeTemplate],
  );
  const scenarioSeries = buildScenarioSeries(costInfl, inflationScenarios);
  const hicpProjections = buildHicpProjections(
    latest,
    inflationScenarios,
    projectionHorizonYears,
  );

  return (
    <Stack spacing={2}>
      <PageHeader
        section="Economic Engine"
        title={
          tab === "curves"
            ? `Curves — ${activeTemplate?.valuationDate ?? "no template selected"}`
            : "Inflation"
        }
        description={
          tab === "curves"
            ? "Select or create a bundle of interest, inflation, HICP and equity-adjustment inputs to use as the economic basis."
            : "Select an economic data template to view its cost-inflation and HICP projections."
        }
        icon={<ShowChartIcon fontSize="small" />}
        statusLabel="Live"
      />

      <TemplatePicker />

      <Tabs
        value={tab}
        onChange={(_, value: Tab) => router.push(ROUTES[value])}
      >
        <Tab value="curves" label="Curves" />
        <Tab value="inflation" label="Inflation" />
      </Tabs>

      <PageLoadingOverlay
        loading={isLoadingTemplates || (Boolean(activeTemplate) && isLoadingRun)}
        label={tab === "curves" ? "Curves" : "Inflation"}
      >
        {!activeTemplate && (
          <Alert severity="warning">
            No template selected — select one above to see its economic data.
          </Alert>
        )}

        {activeTemplate && !isLoadingRun && !run && !activeTemplate.lastRun && (
          <Alert
            severity="info"
            action={
              <Button
                color="inherit"
                size="small"
                onClick={() => router.push("/economic/templates")}
              >
                Go run it
              </Button>
            }
          >
            &quot;{activeTemplate.name}&quot; hasn&apos;t been run yet
            {tab === "inflation" ? " — showing a sample curve below." : "."}
          </Alert>
        )}

        {activeTemplate && !isLoadingRun && !run && activeTemplate.lastRun && (
          <Alert
            severity="warning"
            action={
              <Button
                color="inherit"
                size="small"
                onClick={() => router.push("/economic/templates")}
              >
                Re-run
              </Button>
            }
          >
            &quot;{activeTemplate.name}&quot; last ran successfully at{" "}
            {fmtDate(activeTemplate.lastRun.ranAt)}, but the detailed{" "}
            {tab === "curves" ? "curve" : "inflation"} data isn&apos;t available
            right now (storage unreachable)
            {tab === "inflation"
              ? " — showing a sample curve below, re-run it to refresh."
              : " — re-run it to refresh."}
          </Alert>
        )}

        {tab === "curves" ? (
          <>
            <CurveSetControl
              curveSet={curveSet}
              onCurveSetChange={(cs: CurveSet) => setCurveSet(cs)}
            />
            <CurveKpiRow kpis={kpis} />
            <CurveRateChart
              curveSet={curveSet}
              baseScenario={baseScenario}
              upScenario={upScenario}
              downScenario={downScenario}
              customScenarios={customScenarios}
            />
          </>
        ) : (
          <>
            <InflationKpiRow
              costInfl={costInfl}
              latest={latest}
              indexName={indexName}
            />
            <Stack spacing={2}>
              <InflationCurveChart
                costInfl={costInfl}
                scenarioSeries={scenarioSeries}
              />
              <HicpProjectionChart
                indexName={indexName}
                observed={observed}
                hicpProjections={hicpProjections}
              />
            </Stack>
          </>
        )}
      </PageLoadingOverlay>
    </Stack>
  );
}
