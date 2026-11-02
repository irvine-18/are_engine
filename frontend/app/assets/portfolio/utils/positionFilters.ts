import type { PositionRow } from "@/lib/sampleData/portfolio";

export const FILTER_FIELDS: Array<{ key: "modellingClass" | "cqs" | "country" | "status"; label: string }> = [
  { key: "modellingClass", label: "Modelling class" },
  { key: "cqs", label: "CQS" },
  { key: "country", label: "Country" },
  { key: "status", label: "Status" },
];

export function filterPositions(positions: PositionRow[], filters: Record<string, string | null>): PositionRow[] {
  return positions.filter((p) =>
    FILTER_FIELDS.every(({ key }) => {
      const active = filters[key];
      if (!active) return true;
      return String(p[key]) === active;
    }),
  );
}
