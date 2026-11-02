"use client";

import { IconButton, Stack, Tooltip, useColorScheme } from "@mui/material";
import LightModeIcon from "@mui/icons-material/LightMode";
import DarkModeIcon from "@mui/icons-material/DarkMode";

/** Theme toggle -- the remaining part of the old "Run Context" header bar
 * (`RunContextBar`, removed) that wasn't actually about run context
 * (valuation date/currency/curve set, now owned by the active economic
 * data template instead). Kept in the header since it's genuinely global,
 * not tied to any one page or template. */
export function HeaderActions() {
  const { mode, setMode } = useColorScheme();

  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ flex: 1, justifyContent: "flex-end" }}>
      <Tooltip title="Toggle light/dark mode">
        <IconButton size="small" onClick={() => setMode(mode === "dark" ? "light" : "dark")} aria-label="toggle theme">
          {mode === "dark" ? <LightModeIcon fontSize="small" /> : <DarkModeIcon fontSize="small" />}
        </IconButton>
      </Tooltip>
    </Stack>
  );
}
