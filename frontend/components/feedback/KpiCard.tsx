"use client";

import { Paper, Stack, SxProps, Theme, Tooltip, Typography } from "@mui/material";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

import { isNegative } from "@/lib/format";

interface KpiCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaNegative?: boolean;
  tooltip?: string;
  sx?: SxProps<Theme>;
}

export function KpiCard({ label, value, delta, deltaNegative, tooltip, sx }: KpiCardProps) {
  return (
    <Paper sx={{ p: 2, minWidth: 160, flex: 1, ...sx }}>
      <Stack spacing={0.5}>
        <Stack direction="row" spacing={0.5} alignItems="center">
          <Typography variant="caption" color="text.secondary">
            {label}
          </Typography>
          {tooltip && (
            <Tooltip title={tooltip}>
              <InfoOutlinedIcon sx={{ fontSize: 14, color: "text.secondary" }} />
            </Tooltip>
          )}
        </Stack>
        <Typography
          variant="number"
          sx={{ fontSize: "1.5rem", fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}
        >
          {value}
        </Typography>
        {delta && (
          <Typography variant="number" sx={{ fontSize: "0.8rem" }} color={deltaNegative || isNegative(parseFloat(delta)) ? "error.main" : "success.main"}>
            {delta}
          </Typography>
        )}
      </Stack>
    </Paper>
  );
}
