import { Stack } from "@mui/material";
import { BarChart } from "@mui/x-charts/BarChart";

import { ChartCard } from "@/components/charts/ChartCard";
import { DataTable } from "@/components/data/DataTable";
import { fmtMillions, fmtMoney } from "@/lib/format";
import { bucketByMaturity } from "../utils/maturityBuckets";
import type { EnrichedPositionResult } from "../utils/joinResults";

/** Buckets off the run's own `created_at` (no separate "valuation date" field exists
 * on a Portfolio/Run) -- see `utils/maturityBuckets.ts`. */
export function MaturityBucketsTab({ rows, asOf }: { rows: EnrichedPositionResult[]; asOf: Date }) {
  const buckets = bucketByMaturity(rows, asOf);

  return (
    <Stack spacing={2}>
      <ChartCard
        title="Market value and SCR by maturity bucket"
        chart={
          <BarChart
            height={360}
            margin={{ bottom: 80 }}
            series={[
              { data: buckets.map((b) => b.marketValue), label: "Market value" },
              { data: buckets.map((b) => b.scrTotal), label: "SCR total" },
            ]}
            xAxis={[
              {
                data: buckets.map((b) => b.bucket),
                scaleType: "band",
                tickLabelInterval: () => true,
                tickLabelStyle: { angle: -35, textAnchor: "end" },
              },
            ]}
            yAxis={[{ valueFormatter: (value: number) => fmtMillions(value) }]}
            barLabel={(item) => fmtMillions(item.value)}
          />
        }
        table={
          <DataTable
            height={320}
            fileName="maturity-buckets"
            rows={buckets}
            columns={[
              { field: "bucket", headerName: "Bucket", flex: 1, minWidth: 220 },
              { field: "positionCount", headerName: "Positions", type: "number", width: 100 },
              { field: "marketValue", headerName: "MV", type: "number", flex: 1, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
              { field: "scrTotal", headerName: "SCR Total", type: "number", flex: 1, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
            ]}
          />
        }
      />
    </Stack>
  );
}
