import type { ShockTablePoint } from "@/lib/api/types";
import type { InterestScrShocks } from "@/lib/economicTemplates";

/** Deterministic mock stand-in for EIOPA's published monthly SCR interest-rate shock
 * table (the "revised" methodology's absolute, per-maturity up/down shocks -- as
 * opposed to "standard_formula"'s fixed regulation table, which doesn't vary by
 * month and so has nothing for a publication-month picker to select) -- there's no
 * live feed in this local build, so the same "YYYY-MM" always resolves to the same
 * illustrative table. Maturities and base shapes mirror
 * `backend/src/services/economic_service.py`'s `DEFAULT_INTEREST_SHOCK_TABLE`; each
 * month jitters both shocks within a small band around that shape. */
export function getEiopaScrShocks(month: string): Pick<InterestScrShocks, "methodology" | "table"> {
  function unit(seed: string): number {
    let hash = 0;
    for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) | 0;
    return (Math.abs(hash) % 10000) / 10000; // 0..1
  }

  const base: [number, number, number][] = [
    [1, 0.7, 0.75],
    [5, 0.7, 0.46],
    [10, 0.56, 0.31],
    [15, 0.52, 0.27],
    [20, 0.49, 0.26],
    [90, 0.2, 0.2],
  ];

  const table: ShockTablePoint[] = base.map(([maturity_years, up, down]) => {
    const upJitter = (unit(`${month}-${maturity_years}-up`) - 0.5) * 0.06; // +/-3pp
    const downJitter = (unit(`${month}-${maturity_years}-down`) - 0.5) * 0.06;
    return {
      maturity_years,
      up: Math.round(Math.min(1, Math.max(0, up + upJitter)) * 1000) / 1000,
      down: Math.round(Math.min(1, Math.max(0, down + downJitter)) * 1000) / 1000,
    };
  });

  return { methodology: "revised_2026", table };
}
