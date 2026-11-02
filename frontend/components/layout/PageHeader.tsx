"use client";

import type { ReactNode } from "react";
import { Box, Chip, Stack, Typography } from "@mui/material";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";

interface PageHeaderProps {
  section: string;
  title: string;
  description?: string;
  icon?: ReactNode;
  statusLabel?: string;
  actions?: ReactNode;
}

export function PageHeader({ section, title, description, icon, statusLabel, actions }: PageHeaderProps) {
  return (
    <Stack spacing={1.5} sx={{ mb: 3 }}>
      <Stack direction="row" alignItems="center" spacing={0.5}>
        <Typography variant="overline" color="text.secondary">
          Workspace
        </Typography>
        <ChevronRightIcon sx={{ fontSize: 14, color: "text.secondary" }} />
        <Typography variant="overline" color="text.secondary">
          {section}
        </Typography>
      </Stack>

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "flex-end" }}
      >
        <Stack spacing={1} sx={{ minWidth: 0 }}>
          <Stack direction="row" spacing={1.25} alignItems="center">
            {icon && (
              <Box
                sx={{
                  display: "grid",
                  placeItems: "center",
                  width: 36,
                  height: 36,
                  borderRadius: 2,
                  border: 1,
                  borderColor: "divider",
                  bgcolor: "background.paper",
                  color: "primary.main",
                  flexShrink: 0,
                  boxShadow: "0 1px 2px rgba(16, 17, 30, 0.04)",
                }}
              >
                {icon}
              </Box>
            )}
            <Typography variant="h5">{title}</Typography>
          </Stack>
          {description && (
            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 760, lineHeight: 1.6 }}>
              {description}
            </Typography>
          )}
        </Stack>

        <Stack direction="row" spacing={1} alignItems="center" sx={{ flexShrink: 0 }}>
          {actions}
          {statusLabel && (
            <Chip
              variant="outlined"
              icon={<FiberManualRecordIcon sx={{ fontSize: "8px !important", color: "primary.main" }} />}
              label={statusLabel}
            />
          )}
        </Stack>
      </Stack>
    </Stack>
  );
}
