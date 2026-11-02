import { Stack } from "@mui/material";

import { KpiCard } from "@/components/feedback/KpiCard";
import { fmtRate } from "@/lib/format";
import type { HicpPoint, InflationPoint } from "@/lib/sampleData/inflation";
import type { InflationIndexName } from "./InflationIndexBanner";

interface InflationKpiRowProps {
  costInfl: InflationPoint[];
  latest: HicpPoint;
  indexName: InflationIndexName;
}

export function InflationKpiRow({ costInfl, latest, indexName }: InflationKpiRowProps) {
  return (
    <Stack direction="row" spacing={2} flexWrap="wrap" sx={{ rowGap: 2 }}>
      <KpiCard label="10Y cost inflation" value={fmtRate(costInfl[10]?.rate)} />
      <KpiCard label={`Latest ${indexName}`} value={latest?.index.toFixed(2) ?? "—"} delta={latest?.period} />
      <KpiCard label="Projected HICP +10y (Base)" value={(latest.index * Math.pow(1.021, 10)).toFixed(2)} />
    </Stack>
  );
}
