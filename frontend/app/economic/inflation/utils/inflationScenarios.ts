import { inflationShiftBp, type ScenarioDefinition } from "@/lib/scenarios";
import { projectedHicp, shiftedSeries, type HicpPoint, type InflationPoint } from "@/lib/sampleData/inflation";
import type { EconomicDataTemplate } from "@/lib/economicTemplates";

/** Active scenarios relevant to Inflation — the Base scenario is kept (it drives the HICP
 * projection baseline) even though it carries no inflation shock. */
export function selectInflationScenarios(template: EconomicDataTemplate | undefined): ScenarioDefinition[] {
  if (!template) return [];
  return template.scenarios.filter((s) => s.active && (s.id === "base" || s.inflationShock.type !== "none"));
}

export interface NamedSeries {
  name: string;
  points: InflationPoint[];
  /** Feeds `scenarioColor` (same diverging colour logic Curves uses for its own
   * scenario overlays) so the two pages read as one consistent system. */
  shiftBp: number | null;
}

export function buildScenarioSeries(base: InflationPoint[], scenarios: ScenarioDefinition[]): NamedSeries[] {
  return scenarios
    .filter((s) => s.id !== "base")
    .map((s) => ({ name: s.name, points: shiftedSeries(base, inflationShiftBp(s) ?? 0), shiftBp: inflationShiftBp(s) }));
}

export interface NamedHicpSeries {
  name: string;
  points: HicpPoint[];
  /** Feeds `scenarioColor`, same as `NamedSeries.shiftBp`. */
  shiftBp: number | null;
}

export function buildHicpProjections(latest: HicpPoint, scenarios: ScenarioDefinition[], horizonYears = 15): NamedHicpSeries[] {
  return scenarios.map((s) => ({
    name: s.name,
    points: projectedHicp(latest, 0.021 + (inflationShiftBp(s) ?? 0) / 10000, horizonYears),
    shiftBp: inflationShiftBp(s),
  }));
}
