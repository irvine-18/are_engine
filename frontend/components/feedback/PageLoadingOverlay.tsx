"use client";

import type { ReactNode } from "react";
import { Box, LinearProgress, Stack, Typography } from "@mui/material";

interface PageLoadingOverlayProps {
  loading: boolean;
  /** Shown as "{label} loading…" -- pass the page's own nav label (e.g. "Templates",
   * "SCR Results") so the overlay reads the same regardless of which page it's on. */
  label: string;
  children: ReactNode;
  /** Reserves room for the centered progress bar while `children` has nothing of its
   * own to show yet (e.g. an empty list on first load). */
  minHeight?: number;
  /** Vertical gap between `children`, same as the `Stack` they'd otherwise sit in
   * directly -- this component wraps them in its own `Stack` (needed for the
   * `position: relative` overlay wrapper), so the caller's own spacing would
   * otherwise be lost for a multi-element `children`. */
  spacing?: number;
}

/** Dims a page's body and centers a labeled progress bar over it while that page's
 * primary data is loading -- used right below each nav page's `PageHeader` so the
 * header (and the AppShell sidebar, which lives outside this component entirely)
 * stay put and only the body greys out. */
export function PageLoadingOverlay({ loading, label, children, minHeight = 240, spacing = 2 }: PageLoadingOverlayProps) {
  return (
    <Box sx={{ position: "relative", minHeight: loading ? minHeight : undefined }}>
      <Stack spacing={spacing} sx={{ opacity: loading ? 0.35 : 1, transition: "opacity 0.15s", pointerEvents: loading ? "none" : "auto" }}>
        {children}
      </Stack>
      {loading && (
        <Stack spacing={1.5} alignItems="center" justifyContent="center" sx={{ position: "absolute", inset: 0 }}>
          <Typography variant="body2" color="text.secondary">
            {label} loading…
          </Typography>
          <LinearProgress sx={{ width: 240, borderRadius: 1 }} />
        </Stack>
      )}
    </Box>
  );
}
