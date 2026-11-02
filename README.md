# Asset Risk Engine

A Solvency II-style asset market risk application: build economic scenario data
(interest, inflation, equity, credit spread curves), price individual assets and
portfolios against it, and review SCR (Solvency Capital Requirement) results.

The app is split into two independently-run pieces:

| | Stack | Location |
|---|---|---|
| **Frontend** | Next.js 16 + TypeScript + MUI | [`frontend/`](frontend) |
| **Backend** | Azure Functions (Python) | [`backend/`](backend) |

See [`frontend/README.md`](frontend/README.md) and [`backend/README.md`](backend/README.md)
for stack-specific setup. This file covers how the two fit together and how to run
the whole app locally.

## Architecture

```
frontend (Next.js)  --HTTP-->  backend (Azure Functions)
                                  |
                                  +-- Blob Storage 
                                  |     curve runs, portfolio runs, exports
                                  |
                                  +-- Cosmos DB 
                                  |     templates, portfolios, parameters
                                  |
                                  +-- Model/ 
                                        curve engine, scr model
```

### Request flow (typical)

1. On `/economic/templates`, define a scenario template (interest curve source,
   active scenarios, inflation/equity/credit sections) and hit **Run**. The
   backend prices every active scenario and persists the result plus a flattened
   `asset_rates_table` to Blob Storage, keyed by the template's own id
   (`curve_run_id`).
2. On `/assets/single` or `/assets/portfolio`, pricing requests reference that
   `curve_run_id` to look up the rates table and price assets/positions against
   it — no curve work happens on the asset-pricing endpoints themselves.
3. Results (SCR breakdown, scenario deltas, cashflows) are returned to the
   frontend and rendered; portfolio runs are also persisted so `/assets/runs` can
   list and reopen past runs.

## Key app areas

| Area | Route | What it does |
|---|---|---|
| Economic Data Templates | `/economic/templates` | Define and run scenario templates (interest/inflation/equity/credit-spread curve configuration, active scenarios) |
| Curves | `/economic/curves` | Inspect the active template's resulting curves |
| Single Asset Calculator | `/assets/single` | Price one instrument against the active template's last run; SCR breakdown, scenario impacts, cashflows |
| Portfolio Construction | `/assets/portfolio` | Build/edit portfolios of positions (manual entry or CSV/XLSX upload) |
| SCR Results | `/assets/runs` | List and reopen past portfolio SCR runs; waterfall, buckets, positions, TPT export |