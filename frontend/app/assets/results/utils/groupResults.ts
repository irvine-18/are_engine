import type { EnrichedPositionResult } from "./joinResults";

export interface GroupedRow {
  id: string;
  group: string;
  positionCount: number;
  marketValue: number;
  scrInterestUp: number;
  scrInterestDown: number;
  scrSpread: number;
  scrEquity: number;
  scrTotal: number;
}

/** Aggregates a run's joined position results by an arbitrary key (modelling
 * class, CQS, country, issuer, ...) -- every number here is a straight sum of real
 * `/runs/{id}/positions` figures, nothing illustrative. */
export function groupResults(rows: EnrichedPositionResult[], keyOf: (row: EnrichedPositionResult) => string | null): GroupedRow[] {
  const groups = new Map<string, GroupedRow>();
  for (const row of rows) {
    const key = keyOf(row) || "Unknown";
    const group = groups.get(key) ?? {
      id: key,
      group: key,
      positionCount: 0,
      marketValue: 0,
      scrInterestUp: 0,
      scrInterestDown: 0,
      scrSpread: 0,
      scrEquity: 0,
      scrTotal: 0,
    };
    group.positionCount += 1;
    group.marketValue += row.marketValue;
    group.scrInterestUp += row.scrInterestUp;
    group.scrInterestDown += row.scrInterestDown;
    group.scrSpread += row.scrSpread;
    group.scrEquity += row.scrEquity;
    group.scrTotal += row.scrTotal;
    groups.set(key, group);
  }
  return [...groups.values()].sort((a, b) => b.marketValue - a.marketValue);
}

export const CQS_LABELS: Record<number, string> = {
  0: "CQS 0 (AAA)",
  1: "CQS 1 (AA)",
  2: "CQS 2 (A)",
  3: "CQS 3 (BBB)",
  4: "CQS 4 (BB)",
  5: "CQS 5 (B)",
  6: "CQS 6 (CCC and below)",
};

export const GROUP_DIMENSIONS: Array<{ label: string; keyOf: (row: EnrichedPositionResult) => string | null }> = [
  { label: "By modelling class", keyOf: (row) => row.modellingClass },
  { label: "By CQS", keyOf: (row) => (row.cqs == null ? null : CQS_LABELS[row.cqs] ?? `CQS ${row.cqs}`) },
  { label: "By country", keyOf: (row) => row.country },
  { label: "By issuer", keyOf: (row) => row.issuer },
];
