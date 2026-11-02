import type { InterestSwParameters } from "@/lib/economicTemplates";

/** Deterministic mock stand-in for EIOPA's published monthly Smith-Wilson
 * parameters (UFR, CRA, VA, convergence point, solved alpha) -- there's no live feed
 * in this local build, so the same "YYYY-MM" always resolves to the same illustrative
 * set. UFR, last liquid point and convergence point are pinned to EIOPA's actual
 * fixed EUR conventions (3.3% UFR, 20y LLP, 60y convergence) since those don't vary
 * month to month; CRA/VA/alpha are the figures that do, so those are hash-derived
 * within the roughly realistic bands the real published series has moved in. */
export function getEiopaSwParameters(
  month: string,
): Pick<InterestSwParameters, "lastLiquidPointYears" | "ufr" | "convergenceYears" | "cra" | "va" | "includeVA" | "alphaAutoSolve" | "alphaManual"> {
  function unit(seed: string): number {
    let hash = 0;
    for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) | 0;
    return (Math.abs(hash) % 10000) / 10000; // 0..1
  }

  const cra = 0.0005 + unit(`${month}-cra`) * 0.001; // 5bp .. 15bp
  const va = unit(`${month}-va`) * 0.0025; // 0bp .. 25bp
  const alpha = 0.08 + unit(`${month}-alpha`) * 0.07; // 0.08 .. 0.15

  return {
    lastLiquidPointYears: 20,
    ufr: 0.033,
    convergenceYears: 60,
    cra: Math.round(cra * 1e6) / 1e6,
    va: Math.round(va * 1e6) / 1e6,
    includeVA: true,
    alphaAutoSolve: false,
    alphaManual: Math.round(alpha * 1e4) / 1e4,
  };
}
