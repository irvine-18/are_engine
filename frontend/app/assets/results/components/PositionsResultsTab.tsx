import { useState } from "react";
import { Button, Divider, Drawer, Stack, Typography } from "@mui/material";

import { DataTable } from "@/components/data/DataTable";
import { KpiCard } from "@/components/feedback/KpiCard";
import { fmtMoney } from "@/lib/format";
import type { EnrichedPositionResult } from "../utils/joinResults";

export function PositionsResultsTab({ rows }: { rows: EnrichedPositionResult[] }) {
  const [selected, setSelected] = useState<EnrichedPositionResult | null>(null);

  return (
    <>
      <DataTable
        height={560}
        fileName="run-positions"
        rows={rows}
        columns={[
          { field: "id", headerName: "ID", width: 160 },
          {
            field: "name",
            headerName: "Name",
            flex: 1,
            minWidth: 200,
            renderCell: (p) => (
              <Button size="small" onClick={() => setSelected(p.row)} sx={{ justifyContent: "flex-start", fontWeight: 600 }}>
                {p.value}
              </Button>
            ),
          },
          { field: "modellingClass", headerName: "Modelling class", width: 170 },
          { field: "marketValue", headerName: "MV", type: "number", width: 130, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
          { field: "rating", headerName: "Rating", width: 90 },
          { field: "cqs", headerName: "CQS", type: "number", width: 70 },
          { field: "scrTotal", headerName: "SCR Total", type: "number", width: 130, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
        ]}
      />

      <Drawer anchor="right" open={Boolean(selected)} onClose={() => setSelected(null)} PaperProps={{ sx: { width: { xs: "100%", sm: 480 }, p: 3 } }}>
        {selected && (
          <Stack spacing={2}>
            <Typography variant="h6">{selected.name}</Typography>
            <Typography variant="body2" color="text.secondary">
              {selected.id} · {selected.modellingClass}
            </Typography>
            <Divider />
            <Stack direction="row" spacing={2} flexWrap="wrap" sx={{ rowGap: 2 }}>
              <KpiCard label="Market value" value={fmtMoney(selected.marketValue, selected.currency)} />
              <KpiCard label="SCR total" value={fmtMoney(selected.scrTotal, selected.currency)} />
              <KpiCard label="Rating" value={selected.rating ?? "n.a."} />
              <KpiCard label="Country" value={selected.country ?? "n.a."} />
            </Stack>
            <Typography variant="subtitle2">SCR breakdown</Typography>
            <DataTable
              height={220}
              fileName="position-scr-breakdown"
              rows={[
                { id: "interest_up", component: "Interest (Up)", value: selected.scrInterestUp },
                { id: "interest_down", component: "Interest (Down)", value: selected.scrInterestDown },
                { id: "spread", component: "Spread", value: selected.scrSpread },
                { id: "equity", component: "Equity", value: selected.scrEquity },
                { id: "total", component: "Total", value: selected.scrTotal },
              ]}
              columns={[
                { field: "component", headerName: "Component", flex: 1 },
                { field: "value", headerName: "SCR", type: "number", flex: 1, valueFormatter: (v) => fmtMoney(v as number, selected.currency) },
              ]}
            />
          </Stack>
        )}
      </Drawer>
    </>
  );
}
