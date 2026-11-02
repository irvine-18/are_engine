import { DEFAULT_INFLATION_RATES } from "@/lib/economicTemplates";
import type { LiquidRatePoint } from "@/lib/api/types";

/** Must cover the model's fixed Cost Inflation tenor set exactly (backend
 * `Inflation.cost_inflation_liquid_tenors`), same as `DEFAULT_INFLATION_TENORS` in
 * `lib/economicTemplates.ts`, so the backend run behind this fallback curve succeeds.
 * Rates come from `DEFAULT_INFLATION_RATES` -- see its comment for the shape/source. */
export const FALLBACK_INFLATION_POINTS: LiquidRatePoint[] = Object.entries(DEFAULT_INFLATION_RATES).map(([t, rate]) => ({
  tenor_years: Number(t),
  rate,
  liquid: true,
  source: "manual",
}));
