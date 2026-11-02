import type { InflationSwParameters } from "@/lib/economicTemplates";

/** Deterministic mock stand-in for EIOPA's published monthly Smith-Wilson
 * parameters for the Cost Inflation curve -- there's no live feed in this local
 * build, so the same "YYYY-MM" always resolves to the same illustrative set.
 * Convergence point is pinned at 60y (same EIOPA EUR convention as interest, see
 * `eiopaSwParameters.ts`); UFR and CRA are the figures that vary, hash-derived
 * within a plausible band. */
export function getEiopaInflationSwParameters(month: string): InflationSwParameters {
  function unit(seed: string): number {
    let hash = 0;
    for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) | 0;
    return (Math.abs(hash) % 10000) / 10000; // 0..1
  }

  const ufr = 0.015 + unit(`${month}-ufr`) * 0.01; // 1.5% .. 2.5%
  const cra = 0.0005 + unit(`${month}-cra`) * 0.001; // 5bp .. 15bp

  return {
    ufr: Math.round(ufr * 1e4) / 1e4,
    cra: Math.round(cra * 1e6) / 1e6,
    convergenceYears: 60,
  };
}
