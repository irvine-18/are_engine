import type { LiquidRatePoint } from "@/lib/api/types";

export function rowsFromPoints(points: LiquidRatePoint[]) {
  return points.map((p, idx) => ({ id: idx + 1, ...p }));
}
