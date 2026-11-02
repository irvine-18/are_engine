"use client";

import { useState, type ReactNode } from "react";
import { Box, IconButton, Paper, Stack, ToggleButton, ToggleButtonGroup, Tooltip, Typography } from "@mui/material";
import TableRowsIcon from "@mui/icons-material/TableRows";
import ShowChartIcon from "@mui/icons-material/ShowChart";
import DownloadIcon from "@mui/icons-material/Download";

interface ChartCardProps {
  title: string;
  chart: ReactNode;
  table?: ReactNode;
  actions?: ReactNode;
  onDownloadData?: () => void;
}

export function ChartCard({ title, chart, table, actions, onDownloadData }: ChartCardProps) {
  const [view, setView] = useState<"chart" | "table">("chart");

  return (
    <Paper sx={{ p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          {title}
        </Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          {actions}
          {table && (
            <ToggleButtonGroup
              size="small"
              exclusive
              value={view}
              onChange={(_, v) => v && setView(v)}
              aria-label="chart or table view"
            >
              <ToggleButton value="chart" aria-label="chart view">
                <ShowChartIcon fontSize="small" />
              </ToggleButton>
              <ToggleButton value="table" aria-label="accessible data table">
                <TableRowsIcon fontSize="small" />
              </ToggleButton>
            </ToggleButtonGroup>
          )}
          {onDownloadData && (
            <Tooltip title="Download data (CSV)">
              <IconButton size="small" onClick={onDownloadData} aria-label="download data as CSV">
                <DownloadIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Stack>
      </Stack>
      <Box>{view === "chart" || !table ? chart : table}</Box>
    </Paper>
  );
}
