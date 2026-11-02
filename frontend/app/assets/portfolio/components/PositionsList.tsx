import { useState } from "react";
import { Alert, Chip, MenuItem, Paper, Stack, TextField, Typography } from "@mui/material";

import { DataTable } from "@/components/data/DataTable";
import { fmtMoney } from "@/lib/format";
import type { PositionRow } from "@/lib/sampleData/portfolio";
import { FILTER_FIELDS, filterPositions } from "../utils/positionFilters";

interface PositionsListProps {
  positions: PositionRow[];
}

/** Rendered directly below `UploadPositionsPanel` (not a separate tab/step) --
 * reflects whatever that panel's upload or manual add just produced, since both
 * mutations invalidate the same `usePositions` query `PortfolioDetailView` passes
 * down as `positions`. */
export function PositionsList({ positions }: PositionsListProps) {
  const [filters, setFilters] = useState<Record<string, string | null>>({});

  const filtered = filterPositions(positions, filters);

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Positions
      </Typography>
      <Stack spacing={2}>
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" sx={{ rowGap: 1 }}>
          {FILTER_FIELDS.map(({ key, label }) => {
            const options = Array.from(new Set(positions.map((p) => String(p[key]))));
            return (
              <TextField
                key={key}
                select
                size="small"
                label={label}
                value={filters[key] ?? ""}
                onChange={(e) => setFilters((f) => ({ ...f, [key]: e.target.value || null }))}
                sx={{ minWidth: 150 }}
              >
                <MenuItem value="">All</MenuItem>
                {options.map((o) => (
                  <MenuItem key={o} value={o}>
                    {o}
                  </MenuItem>
                ))}
              </TextField>
            );
          })}
        </Stack>

        {positions.length === 0 ? (
          <Alert severity="info">No positions yet. Upload a file or add one manually above.</Alert>
        ) : (
          <DataTable
            height={560}
            fileName="positions"
            rows={filtered}
            columns={[
              { field: "id", headerName: "ID", width: 100 },
              { field: "name", headerName: "Name", flex: 1, minWidth: 200 },
              { field: "modellingClass", headerName: "Modelling class", width: 170 },
              { field: "cic", headerName: "CIC", width: 80 },
              { field: "currency", headerName: "Ccy", width: 70 },
              { field: "nominal", headerName: "Nominal", type: "number", width: 130, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
              { field: "marketValue", headerName: "MV", type: "number", width: 130, valueFormatter: (v) => fmtMoney(v as number, undefined, true) },
              { field: "rating", headerName: "Rating", width: 80 },
              { field: "cqs", headerName: "CQS", type: "number", width: 70 },
              { field: "maturity", headerName: "Maturity", width: 110 },
              { field: "issuer", headerName: "Issuer", width: 170 },
              { field: "country", headerName: "Country", width: 90 },
              { field: "included", headerName: "Included", type: "boolean", width: 90, editable: true },
              {
                field: "status",
                headerName: "Status",
                width: 100,
                renderCell: (p) =>
                  p.value === "ok" ? (
                    <Chip size="small" color="success" label="OK" />
                  ) : p.value === "warning" ? (
                    <Chip size="small" color="warning" label="Warning" />
                  ) : (
                    <Chip size="small" color="error" label="Error" />
                  ),
              },
            ]}
          />
        )}
      </Stack>
    </Paper>
  );
}
