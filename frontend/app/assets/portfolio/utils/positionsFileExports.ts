import * as XLSX from "xlsx";

import { makePositions, type PositionRow } from "@/lib/sampleData/portfolio";

/** The app's own required/optional column names for "Upload Positions File" --
 * matches `_COLUMN_ALIASES` in backend/src/services/portfolio_service.py exactly
 * (lowercase, snake_case), so a file downloaded here re-uploads without edits.
 * `name` and `market_value` are required; everything else is optional and falls
 * back to a defaulted value (see that module's `parse_positions_file`). The
 * remaining columns (`next_coupon_date` onward) match `AssetPropertiesInput`'s own
 * field names exactly -- `_asset_detail_from_row` in that same backend module picks
 * them up by exact name, so a position imported from this file actually gets priced
 * by the real engine (`services/run_service.py`), not just displayed. Previously
 * this sample only had the first 9 columns, so every position it produced imported
 * fine but had no pricing detail at all -- a portfolio run against it always
 * resolved to zero positions priced (see `run_service.py`'s "no pricing detail
 * captured" error) despite looking like a normal, successful run. */
export const SAMPLE_PORTFOLIO_COLUMNS = [
  "name",
  "modelling_class",
  "market_value",
  "nominal",
  "rating",
  "maturity_date",
  "issuer",
  "country",
  "currency",
  "next_coupon_date",
  "coupon_frequency",
  "annual_fixed_coupon_rate",
  "annual_nominal_coupon_rate",
  "annual_floating_coupon_rate",
  "annual_coupon_spread",
  "annual_fixed_interest_rate",
  "modified_duration",
  "swap_term",
  "inflation_index",
  "inflation_index_lag",
  "current_indexation_coefficient",
  "equity_type",
];

const SAMPLE_PORTFOLIO_SIZE = 8;

// A fixed near-term date, safely before every maturity `makePositions` generates
// (2027 onward) -- good enough for an illustrative sample file, not meant to be a
// realistic coupon schedule (same spirit as `makePositions`' own seeded-random
// maturities/ratings).
const SAMPLE_NEXT_COUPON_DATE = "2026-12-15";

/** Per-class fields `services/portfolio_service.py::_asset_detail_from_row` needs to
 * actually price a position -- mirrors `frontend/app/assets/single/utils/
 * buildAssetInput.ts`'s own per-class field requirements, with fixed illustrative
 * values instead of reading a form. Blank object for classes needing nothing beyond
 * the common columns above (e.g. `cash`). */
function pricingDetailFor(modellingClass: string, index: number): Record<string, string | number> {
  switch (modellingClass) {
    case "gvt_bond_fixed_coupon":
      return { next_coupon_date: SAMPLE_NEXT_COUPON_DATE, coupon_frequency: 1, annual_fixed_coupon_rate: 0.02 + (index % 4) / 100 };
    case "gvt_bond_inflation_linked":
      return {
        next_coupon_date: SAMPLE_NEXT_COUPON_DATE,
        coupon_frequency: 1,
        annual_nominal_coupon_rate: 0.01,
        inflation_index: "hicp",
        inflation_index_lag: 3,
        current_indexation_coefficient: 1.05,
      };
    case "corp_bond_fixed_coupon":
      return {
        next_coupon_date: SAMPLE_NEXT_COUPON_DATE,
        coupon_frequency: 2,
        annual_fixed_coupon_rate: 0.03 + (index % 4) / 100,
        modified_duration: 4 + (index % 8),
      };
    case "corp_bond_floating_interest":
      return {
        next_coupon_date: SAMPLE_NEXT_COUPON_DATE,
        coupon_frequency: 4,
        annual_floating_coupon_rate: 0.032,
        annual_coupon_spread: 0.006,
        modified_duration: 3 + (index % 6),
      };
    case "irs_fixed":
      return { next_coupon_date: SAMPLE_NEXT_COUPON_DATE, coupon_frequency: 1, annual_fixed_interest_rate: 0.028, swap_term: 10 };
    case "equity":
      return { equity_type: 1 };
    case "cash":
    default:
      return {};
  }
}

function toSampleRow(p: PositionRow, index: number) {
  return {
    name: p.name,
    modelling_class: p.modellingClass,
    market_value: p.marketValue,
    nominal: p.nominal,
    rating: p.rating,
    maturity_date: p.maturity ?? "",
    issuer: p.issuer,
    country: p.country,
    currency: p.currency,
    ...pricingDetailFor(p.modellingClass, index),
  };
}

export function downloadSamplePortfolio() {
  const sample = makePositions(SAMPLE_PORTFOLIO_SIZE).map(toSampleRow);
  const sheet = XLSX.utils.json_to_sheet(sample, { header: SAMPLE_PORTFOLIO_COLUMNS });
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, sheet, "Sample portfolio");
  XLSX.writeFile(workbook, "sample-portfolio.xlsx");
}
