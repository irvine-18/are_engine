/** Deterministic mock stand-in for EIOPA's published monthly equity symmetric adjustment
 * (Solvency II Article 172) -- there's no live feed in this local build, so the same
 * "YYYY-MM" always resolves to the same illustrative value, within the roughly -9%..+6%
 * band the real published series has moved in historically. */
export function getEiopaSymmetricAdjustment(month: string): number {
  let hash = 0;
  for (let i = 0; i < month.length; i++) {
    hash = (hash * 31 + month.charCodeAt(i)) | 0;
  }
  const unit = (Math.abs(hash) % 10000) / 10000; // 0..1
  const value = -0.09 + unit * 0.15; // -9% .. +6%
  return Math.round(value * 10000) / 10000;
}
