import type { InflationPoint } from "@/lib/sampleData/inflation";
import type { ScenarioCurve } from "@/lib/api/types";

/** Works for either `TemplateCurveRunResult.inflation` or `.cost_inflation` -- same
 * scenario/shock shape, just sourced from a different rates set on the backend. */
export function selectBaseScenario(scenarios: ScenarioCurve[] | undefined): ScenarioCurve | undefined {
  return scenarios?.find((s) => s.scenario === "Base" && s.shock === "base");
}

/** `undefined` (rather than an empty array) when there's nothing to show yet, so
 * callers can fall back to the illustrative mock series with `??`. */
export function scenarioCurveToInflationPoints(curve: ScenarioCurve | undefined): InflationPoint[] | undefined {
  if (!curve || curve.annual.length === 0) return undefined;
  return curve.annual.map((p) => ({ year: p.year ?? 0, rate: p.spot_rate }));
}
