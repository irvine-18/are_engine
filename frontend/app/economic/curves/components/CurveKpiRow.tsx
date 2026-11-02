import { Stack } from "@mui/material";

import { KpiCard } from "@/components/feedback/KpiCard";
import { fmtRate } from "@/lib/format";
import type { CurveRunKpis } from "@/lib/api/types";

interface CurveKpiRowProps {
  kpis: CurveRunKpis | undefined;
}

export function CurveKpiRow({ kpis }: CurveKpiRowProps) {
  return (
    <Stack direction="row" spacing={2} flexWrap="wrap">
      <KpiCard label="10y spot" value={fmtRate(kpis?.spot_10y)} />
      <KpiCard label="20y spot" value={fmtRate(kpis?.spot_20y)} />
      <KpiCard label="30y spot" value={fmtRate(kpis?.spot_30y)} />
      <KpiCard label="60y forward" value={fmtRate(kpis?.forward_60y)} />
    </Stack>
  );
}
