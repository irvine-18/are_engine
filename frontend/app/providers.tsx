"use client";

import { useState, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";

import { theme } from "@/theme/theme";
import { AppShell } from "@/components/layout/AppShell";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 30_000 } } }));

  return (
    <AppRouterCacheProvider options={{ key: "mui" }}>
      <ThemeProvider theme={theme} defaultMode="light">
        <CssBaseline />
        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <QueryClientProvider client={queryClient}>
            <AppShell>{children}</AppShell>
          </QueryClientProvider>
        </LocalizationProvider>
      </ThemeProvider>
    </AppRouterCacheProvider>
  );
}
