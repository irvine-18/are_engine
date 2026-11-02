# Backend — Asset Risk Engine

Azure Functions (Python) app serving the Asset Risk Engine API. Combines a
standalone pricing/curve model (`src/model/`) with Azure-backed persistence
(Cosmos DB for documents, Blob Storage for curve/run artifacts).

See the [root README](../README.md) for how this fits together with the frontend.

## Stack

- Azure Functions (Python, HTTP-triggered blueprints)
- pandas / numpy / scipy for the pricing and curve-extrapolation model
- pydantic for request/response schemas
- Cosmos DB (templates, portfolios, parameters, reference market data)
- Blob Storage (curve run results, portfolio run results, TPT exports)
- pytest for tests

## Project layout

```
backend/
  function_app.py        # entry point, registers each blueprint
  host.json               # Functions host config (routePrefix "api")
  local.settings.json     # local-only, gitignored — copy from the example below
  requirements.txt
  src/
    api/                   # HTTP blueprints — one file per domain area
      economic_data.py       # /economic-data/* — scenario templates, running them
      curves.py               # /curves/run — ad-hoc curve runs
      assets.py                # /assets/* — sample assets, single-asset pricing
      portfolios.py            # /portfolios/* — CRUD, positions, TPT export, runs
      runs.py                   # /runs/* — list/reopen past portfolio SCR runs
      parameters.py             # /parameters/{valuation_date} — EIOPA parameter sets
      scenarios.py               # /scenarios — scenario catalogue
      jobs.py                     # /jobs/{job_id} — async job status/cancel
      health.py                    # /health
    services/              # glue between model/ and the API layer
    schemas/                # pydantic request/response models
    model/                  # the actual actuarial/financial model
      economic_data/          # curve building, extrapolation, inflation
      asset_risk/              # asset cashflows, z-spread, SCR calculations
      settings/                 # Model Parameters.xlsx / Data Specifications.xlsx
      utilities/
    storage/                # Cosmos + Blob clients
      cosmos.py
      blob.py
      store.py                # higher-level read/write used by the API layer
    config.py                # env var resolution, local emulator defaults
  tests/
    unit/                   # model/service-level tests
    api/                    # HTTP route tests
    regression/
```
