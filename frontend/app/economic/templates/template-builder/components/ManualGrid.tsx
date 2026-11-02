"use client";

import { useEffect } from "react";
import { Alert, Button, IconButton, Stack, Tooltip } from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";

import { rowsFromPoints } from "../utils/rowsFromPoints";
import type { LiquidRatePoint } from "@/lib/api/types";

export function ManualGrid({
  points,
  onChange,
  rateLabel = "Rate (%)",
  height = 360,
  requiredPoints,
}: {
  points: LiquidRatePoint[];
  onChange: (points: LiquidRatePoint[]) => void;
  rateLabel?: string;
  height?: number;
  /** The model's full required tenor set for this curve, each with a sensible
   * placeholder rate -- e.g. `defaultInterestLiquidPoints()`/
   * `defaultInflationLiquidPoints()` (`@/lib/economicTemplates`). Any tenor missing
   * from `points` is silently backfilled from here (an incomplete set otherwise runs
   * fine but silently zeroes the dependent curve -- see those functions' docstring),
   * and present rows for these tenors can't be deleted. Omit for a grid with no
   * required tenors (none currently, but keeps this component reusable). */
  requiredPoints?: LiquidRatePoint[];
}) {
  const requiredTenors = new Set(requiredPoints?.map((p) => p.tenor_years) ?? []);

  useEffect(() => {
    if (!requiredPoints) return;
    const present = new Set(points.map((p) => p.tenor_years));
    const missing = requiredPoints.filter((p) => !present.has(p.tenor_years));
    if (missing.length > 0) onChange([...points, ...missing]);
    // Only re-check when the points/required set actually change, not on every
    // parent re-render -- `onChange` is a setter, stable enough not to need listing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points, requiredPoints]);

  const rows = rowsFromPoints(points);

  const columns: GridColDef[] = [
    { field: "tenor_years", headerName: "Tenor (years)", type: "number", flex: 1, editable: true },
    {
      field: "rate",
      headerName: rateLabel,
      type: "number",
      flex: 1,
      editable: true,
      valueGetter: (value) => (typeof value === "number" ? Number((value * 100).toFixed(4)) : value),
      valueSetter: (value, row) => ({ ...row, rate: Number(value) / 100 }),
    },
    { field: "liquid", headerName: "Liquid", type: "boolean", flex: 1, editable: true },
    { field: "source", headerName: "Source", flex: 1, editable: true },
    ...(requiredPoints
      ? [
          {
            field: "required",
            headerName: "Required",
            type: "boolean",
            flex: 0.7,
            sortable: false,
            valueGetter: (_value: unknown, row: { tenor_years: number }) => requiredTenors.has(row.tenor_years),
          } satisfies GridColDef,
        ]
      : []),
    {
      field: "actions",
      headerName: "",
      width: 60,
      renderCell: (params) =>
        requiredTenors.has(params.row.tenor_years) ? (
          <Tooltip title="Required by the model — can't be removed">
            <span>
              <IconButton size="small" aria-label="remove row" disabled>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        ) : (
          <IconButton size="small" aria-label="remove row" onClick={() => onChange(points.filter((_, idx) => idx + 1 !== params.row.id))}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        ),
    },
  ];

  const sorted = [...points].sort((a, b) => a.tenor_years - b.tenor_years);
  const duplicateTenors = sorted.some((p, i) => i > 0 && p.tenor_years === sorted[i - 1].tenor_years);
  const outOfRange = points.some((p) => p.rate < -0.02 || p.rate > 0.15);

  return (
    <Stack spacing={1}>
      {duplicateTenors && <Alert severity="warning">Duplicate tenors found.</Alert>}
      {outOfRange && <Alert severity="warning">One or more rates are outside the expected -2%…15% range.</Alert>}
      <div style={{ height, width: "100%" }}>
        <DataGrid
          density="compact"
          rows={rows}
          columns={columns}
          editMode="row"
          processRowUpdate={(updated) => {
            const next = points.map((p, idx) => (idx + 1 === updated.id ? { tenor_years: updated.tenor_years, rate: updated.rate, liquid: updated.liquid, source: updated.source } : p));
            onChange(next);
            return updated;
          }}
          hideFooterPagination
          hideFooterSelectedRowCount
        />
      </div>
      <Button
        size="small"
        startIcon={<AddIcon />}
        onClick={() => onChange([...points, { tenor_years: 0, rate: 0, liquid: false, source: "manual" }])}
        sx={{ alignSelf: "flex-start" }}
      >
        Add row
      </Button>
    </Stack>
  );
}
