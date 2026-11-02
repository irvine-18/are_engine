import type { EconomicDataTemplate } from "@/lib/economicTemplates";

export function validateTemplate(template: EconomicDataTemplate): string | null {
  if (!template.valuationDate) {
    return "Set a valuation date.";
  }
  if (!Number.isFinite(template.projectionHorizonYears) || template.projectionHorizonYears <= 0) {
    return "Set a positive projection horizon.";
  }
  if (!template.name.trim()) {
    return "Give the template a name.";
  }
  if (
    !template.interest.included &&
    !template.inflation.included &&
    !template.hicp.included &&
    !template.equity.included &&
    !template.creditSpread.included
  ) {
    return "Include at least one of Interest, Inflation, HICP, Equity Adjustment or Credit Spread.";
  }
  // `Inflation.get_hicp` (backend/src/model/economic_data/inflation.py) filters HICP
  // observations to strictly before the valuation date, then does `.iloc[0]` on
  // whatever's left with no bounds check -- an observation dated on or after the
  // valuation date passes every upstream check (including the backend's own
  // run-time fallback, which only kicks in when the date is *missing*, not invalid)
  // and crashes deep in the model with `IndexError: single positional indexer is
  // out-of-bounds`, with the real cause nowhere in sight. ISO date strings compare
  // correctly as plain strings here.
  if (
    template.hicp.included &&
    template.hicp.latestObservationDate &&
    template.hicp.latestObservationDate >= template.valuationDate
  ) {
    return "HICP's latest observation date must be strictly before the valuation date.";
  }
  return null;
}
