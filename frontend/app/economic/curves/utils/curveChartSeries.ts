import { interestShiftBp, type ScenarioDefinition } from "@/lib/scenarios";
import { scenarioColor } from "@/lib/scenarioColor";
import type { CurvePoint, ScenarioCurve } from "@/lib/api/types";

function pointValue(point: CurvePoint) {
  return point.spot_rate * 100;
}

export interface CurveLineSeries {
  id: string;
  data: number[];
  label: string;
  color: string;
}

export function buildCurveLineSeries(
  mode: "light" | "dark",
  baseScenario: ScenarioCurve | undefined,
  upScenario: ScenarioCurve | undefined,
  downScenario: ScenarioCurve | undefined,
  customScenarios: ScenarioDefinition[],
): CurveLineSeries[] {
  if (!baseScenario) return [];

  const series: CurveLineSeries[] = [
    { id: "base", data: baseScenario.annual.map(pointValue), label: "Base", color: scenarioColor(mode, 0) },
  ];

  if (upScenario) {
    series.push({ id: "scr-up", data: upScenario.annual.map(pointValue), label: "SCR Interest Up", color: scenarioColor(mode, 100) });
  }
  if (downScenario) {
    series.push({ id: "scr-down", data: downScenario.annual.map(pointValue), label: "SCR Interest Down", color: scenarioColor(mode, -100) });
  }

  for (const scenario of customScenarios) {
    const representativeShiftBp = interestShiftBp(scenario, pointValue(baseScenario.annual[0]));
    series.push({
      id: scenario.id,
      data: baseScenario.annual.map((p) => {
        const basePct = pointValue(p);
        const shiftBp = interestShiftBp(scenario, basePct) ?? 0;
        return basePct + shiftBp / 100;
      }),
      label: scenario.name,
      color: scenarioColor(mode, representativeShiftBp),
    });
  }

  return series;
}

export function curveChartYears(baseScenario: ScenarioCurve | undefined): number[] {
  return baseScenario?.annual.map((p) => p.year ?? 0) ?? [];
}
