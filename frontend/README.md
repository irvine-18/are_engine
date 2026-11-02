# Frontend — Asset Risk Engine

Next.js (TypeScript) UI for the Asset Risk Engine: build economic scenario
templates, price single assets or portfolios against them, and review SCR
results.

See the [root README](../README.md) for how this fits together with the backend.

## Stack

- Next.js 16 (App Router) + TypeScript
- Material UI (`@mui/material`, `@mui/icons-material`, `@mui/x-data-grid`, `@mui/x-charts`, `@mui/x-date-pickers`)

## Project layout

```
frontend/
  app/
    economic/
      templates/        # /economic/templates — build & run scenario templates
      curves/            # /economic/curves — inspect the active template's curves
      inflation/          # cost-inflation curve detail
    assets/
      single/            # /assets/single — Single Asset Calculator
      portfolio/          # /assets/portfolio — portfolio construction
      runs/                # /assets/runs — SCR run history
      results/              # portfolio run results (SCR breakdown, buckets, positions)
  components/            # shared UI (layout shell, data tables, charts, feedback)
  lib/
    api/                  # typed API client + TanStack Query hooks
    economicTemplates.ts    # template model/helpers
    scenarios.ts              # scenario definitions (built-in + quick-add presets)
    format.ts                  # number/date formatters
  stores/                # zustand stores (e.g. active economic template)
  theme/                 # MUI theme
```
