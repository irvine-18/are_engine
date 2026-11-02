import type { ReactNode } from "react";
import { Box, FormControlLabel, Stack, Switch, Typography } from "@mui/material";

export function SectionHeader({
  icon,
  title,
  included,
  onIncludedChange,
}: {
  icon: ReactNode;
  title: string;
  included: boolean;
  onIncludedChange: (v: boolean) => void;
}) {
  return (
    <Stack direction="row" spacing={1.5} alignItems="center" sx={{ width: "100%" }}>
      <Box sx={{ display: "flex", color: "primary.main" }}>{icon}</Box>
      <Typography sx={{ flex: 1 }} fontWeight={600}>
        {title}
      </Typography>
      <FormControlLabel
        label={included ? "Included" : "Not included"}
        labelPlacement="start"
        control={
          <Switch size="small" checked={included} onClick={(e) => e.stopPropagation()} onChange={(e) => onIncludedChange(e.target.checked)} />
        }
        sx={{ mr: 0 }}
      />
    </Stack>
  );
}
