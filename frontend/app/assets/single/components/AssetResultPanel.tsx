import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import { BarChart } from "@mui/x-charts/BarChart";
import PlaylistAddIcon from "@mui/icons-material/PlaylistAdd";

import { KpiCard } from "@/components/feedback/KpiCard";
import { ChartCard } from "@/components/charts/ChartCard";
import { DataTable } from "@/components/data/DataTable";
import { fmtMoney, fmtMonth } from "@/lib/format";
import type { SingleAssetResult } from "@/lib/api/types";

interface AssetResultPanelProps {
  result: SingleAssetResult | undefined;
  onAddToPortfolio: () => void;
  /** True once the form has changed since this result was calculated -- see
   * `SingleAssetPage`'s dirty-state dialog. Greys the result out and blocks "Add to
   * portfolio" rather than letting a stale result be mistaken for the current inputs. */
  dimmed?: boolean;
}

export function AssetResultPanel({ result, onAddToPortfolio, dimmed = false }: AssetResultPanelProps) {
  if (!result) return <Alert severity="info">Fill in the form and click Calculate.</Alert>;

  return (
    <Stack spacing={2} sx={{ opacity: dimmed ? 0.45 : 1, transition: "opacity 0.15s", pointerEvents: dimmed ? "none" : "auto" }}>
      {dimmed && <Alert severity="warning" sx={{ pointerEvents: "auto" }}>These results are stale — recalculate to match your current inputs.</Alert>}
      {result.scenario_errors.length > 0 && (
        <Alert severity="warning" sx={{ pointerEvents: "auto" }}>
          Couldn&apos;t price {result.scenario_errors.length === 1 ? "1 scenario" : `${result.scenario_errors.length} scenarios`} — the rest of
          this result is unaffected: {result.scenario_errors.join("; ")}
        </Alert>
      )}
      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(7, minmax(0, 1fr))", gap: 1.5 }}>
        <KpiCard label="Market value" value={fmtMoney(result.market_value, undefined, true)} sx={{ minWidth: 0 }} />
        <KpiCard label="Z-spread" value={`${result.z_spread_bp.toFixed(1)} bp`} sx={{ minWidth: 0 }} />
        <KpiCard label="DV01" value={fmtMoney(result.dv01)} sx={{ minWidth: 0 }} />
        <KpiCard label="SCR Interest (down)" value={fmtMoney(result.scr.interest_down)} sx={{ minWidth: 0 }} />
        <KpiCard label="SCR Interest (up)" value={fmtMoney(result.scr.interest_up)} sx={{ minWidth: 0 }} />
        <KpiCard label="SCR Spread" value={fmtMoney(result.scr.spread)} sx={{ minWidth: 0 }} />
        <KpiCard label="SCR Equity" value={fmtMoney(result.scr.equity)} sx={{ minWidth: 0 }} />
      </Box>

      <Button size="small" variant="outlined" startIcon={<PlaylistAddIcon />} sx={{ alignSelf: "flex-start" }} onClick={onAddToPortfolio} disabled={dimmed}>
        Add to portfolio
      </Button>

      <ChartCard
        title="Scenario impact vs Base"
        chart={
          <BarChart
            height={260}
            series={[{ data: result.scenario_results.map((s) => s.delta_vs_base), label: "Δ market value" }]}
            xAxis={[{ data: result.scenario_results.map((s) => s.scenario), scaleType: "band" }]}
          />
        }
      />

      <Typography variant="subtitle2">Base-scenario cashflows</Typography>
      <DataTable
        fileName="single-asset-cashflows"
        rows={result.cashflows
          .filter((cf) => cf.scenario === "Base" && cf.shock === "spot_interest")
          .map((cf, idx) => ({ id: idx, ...cf }))}
        columns={[
          { field: "date", headerName: "Month", flex: 1, valueFormatter: (v) => fmtMonth(v as string) },
          { field: "coupon_payment", headerName: "Coupon", type: "number", flex: 1, valueFormatter: (v) => fmtMoney(v as number) },
          { field: "maturity_payment", headerName: "Maturity", type: "number", flex: 1, valueFormatter: (v) => fmtMoney(v as number) },
          { field: "discount_factor", headerName: "DF", type: "number", flex: 1, valueFormatter: (v) => (v as number).toFixed(4) },
          { field: "discounted_cashflow", headerName: "PV", type: "number", flex: 1, valueFormatter: (v) => fmtMoney(v as number) },
        ]}
        height={320}
      />
    </Stack>
  );
}
