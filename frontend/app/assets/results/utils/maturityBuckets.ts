import type { EnrichedPositionResult } from "./joinResults";

export interface MaturityBucketRow {
  id: string;
  bucket: string;
  positionCount: number;
  marketValue: number;
  scrTotal: number;
}

const BUCKET_LABELS = ["0-5Y", "5-10Y", "10-15Y", "15-20Y", "20-25Y", "25Y+"];
const NO_MATURITY_LABEL = "No maturity (cash, equity, derivatives)";

/** Buckets by years between `asOf` (the run's own `created_at` -- portfolios/runs
 * carry no separate "valuation date" field) and each position's `maturityDate`.
 * Positions without one (cash, private equity, several derivative legs) get their
 * own bucket rather than being dropped or guessed at. */
export function bucketByMaturity(rows: EnrichedPositionResult[], asOf: Date): MaturityBucketRow[] {
  const buckets = new Map<string, MaturityBucketRow>();
  const bucketFor = (label: string) => {
    const existing = buckets.get(label);
    if (existing) return existing;
    const created: MaturityBucketRow = { id: label, bucket: label, positionCount: 0, marketValue: 0, scrTotal: 0 };
    buckets.set(label, created);
    return created;
  };

  for (const row of rows) {
    let label = NO_MATURITY_LABEL;
    if (row.maturityDate) {
      const years = (new Date(row.maturityDate).getTime() - asOf.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
      const bucketIndex = Math.min(Math.max(Math.floor(years / 5), 0), BUCKET_LABELS.length - 1);
      label = BUCKET_LABELS[bucketIndex];
    }
    const bucket = bucketFor(label);
    bucket.positionCount += 1;
    bucket.marketValue += row.marketValue;
    bucket.scrTotal += row.scrTotal;
  }

  const order = [...BUCKET_LABELS, NO_MATURITY_LABEL];
  return order.map((label) => buckets.get(label)).filter((b): b is MaturityBucketRow => Boolean(b));
}
