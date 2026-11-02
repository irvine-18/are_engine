import { Stack } from "@mui/material";

import { KpiCard } from "@/components/feedback/KpiCard";
import { fmtMoney } from "@/lib/format";
import type { RunSummary } from "@/lib/api/types";

export function KpiRow({ summary }: { summary: RunSummary }) {
  return (
    <Stack direction="row" spacing={2} flexWrap="wrap" sx={{ rowGap: 2 }}>
      <KpiCard label="Total market value" value={fmtMoney(summary.total_market_value, "EUR", true)} />
      <KpiCard label="Interest SCR (Up)" value={fmtMoney(summary.scr_interest_up, "EUR", true)} />
      <KpiCard label="Interest SCR (Down)" value={fmtMoney(summary.scr_interest_down, "EUR", true)} />
      <KpiCard label="Spread SCR" value={fmtMoney(summary.scr_spread, "EUR", true)} />
      <KpiCard label="Equity SCR" value={fmtMoney(summary.scr_equity, "EUR", true)} />
      <KpiCard label="Positions" value={`${summary.positions_total - summary.positions_errored} / ${summary.positions_total}`} tooltip="Priced / total." />
      <KpiCard label="Currency SCR" value="n.a." tooltip="Not implemented in the engine — see CODE_OVERVIEW.md known gaps." />
    </Stack>
  );
}
