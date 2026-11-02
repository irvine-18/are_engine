import { Box, Stack } from "@mui/material";
import { BarChart } from "@mui/x-charts/BarChart";

import { ChartCard } from "@/components/charts/ChartCard";
import { fmtMillions } from "@/lib/format";
import type { RunSummary } from "@/lib/api/types";
import type { GroupedRow } from "../utils/groupResults";

const SLANTED_X_AXIS = {
  scaleType: "band" as const,
  tickLabelInterval: () => true,
  tickLabelStyle: { angle: -35, textAnchor: "end" as const },
};

/** Right panel is "SCR by modelling class" (real, from the same grouped rows the
 * Grouped tab uses) rather than the old mock's "Scenario impact vs Base" --
 * `services/run_service.py`'s placeholder pricing has no per-scenario breakdown to
 * show one honestly. */
export function WaterfallAndImpact({ summary, byModellingClass }: { summary: RunSummary; byModellingClass: GroupedRow[] }) {
  const waterfall = [
    { label: "Interest (Up)", value: summary.scr_interest_up },
    { label: "Interest (Down)", value: summary.scr_interest_down },
    { label: "Spread", value: summary.scr_spread },
    { label: "Equity", value: summary.scr_equity },
    { label: "Total (pre-diversification)", value: summary.scr_total },
  ];

  return (
    <Stack direction={{ xs: "column", lg: "row" }} spacing={2}>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <ChartCard
          title="SCR waterfall"
          chart={
            <BarChart
              height={340}
              margin={{ bottom: 80 }}
              series={[{ data: waterfall.map((s) => s.value), label: "SCR" }]}
              xAxis={[{ data: waterfall.map((s) => s.label), ...SLANTED_X_AXIS }]}
              yAxis={[{ valueFormatter: (value: number) => fmtMillions(value) }]}
              barLabel={(item) => fmtMillions(item.value)}
              slotProps={{ legend: { hidden: true } }}
            />
          }
        />
      </Box>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <ChartCard
          title="SCR by modelling class"
          chart={
            <BarChart
              height={340}
              margin={{ bottom: 80 }}
              series={[{ data: byModellingClass.map((g) => g.scrTotal), label: "SCR total" }]}
              xAxis={[{ data: byModellingClass.map((g) => g.group), ...SLANTED_X_AXIS }]}
              yAxis={[{ valueFormatter: (value: number) => fmtMillions(value) }]}
              barLabel={(item) => fmtMillions(item.value)}
              slotProps={{ legend: { hidden: true } }}
            />
          }
        />
      </Box>
    </Stack>
  );
}
