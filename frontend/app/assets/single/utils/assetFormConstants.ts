import type { ModellingClass } from "@/lib/api/types";

/** Numeric fields are `number | ""` rather than plain `number` so a cleared
 * TextField is distinguishable from an entered `0` -- `Number("")` is `0`, which
 * would otherwise make "required" validation (`validateAssetForm.ts`) unable to
 * tell a blank field from a legitimately-zero one (e.g. a 0bp floating spread). */
export interface FormState {
  modellingClass: ModellingClass;
  nominal: number | "";
  marketValue: number | "";
  issueDate: string;
  maturityDate: string;
  nextCouponDate: string;
  couponFrequency: number;
  couponRate: number | "";
  floatingSpread: number | "";
  swapTerm: number | "";
  inflationIndexLag: number | "";
  indexationCoefficient: number | "";
  inflationIndexStart: number | "";
  exchangeRate: number | "";
  /** FX forward only -- the deal's notional in the quotation (foreign) currency.
   * Distinct from `nominal` (the portfolio-currency notional): `calc_fx_forwards`
   * (backend/src/model/asset_risk/asset_methods.py) settles the forward as
   * `nominal_quotation_currency / exchange_rate`, so this is what actually drives
   * the payoff, not `nominal`. */
  nominalQuotationCurrency: number | "";
  equityType: number;
  rating: string;
  modifiedDuration: number | "";
}

export const DEFAULT_FORM: FormState = {
  modellingClass: "gvt_bond_fixed_coupon",
  nominal: 1_000_000,
  marketValue: 1_050_000,
  issueDate: "2020-01-15",
  maturityDate: "2034-01-15",
  nextCouponDate: "2025-01-15",
  couponFrequency: 1,
  couponRate: 3.5,
  floatingSpread: 0.6,
  swapTerm: 10,
  inflationIndexLag: 3,
  indexationCoefficient: 1.02,
  inflationIndexStart: 110.5,
  exchangeRate: 1,
  nominalQuotationCurrency: 1_000_000,
  equityType: 1,
  rating: "AAA",
  modifiedDuration: 8.5,
};

export const MODELLING_CLASS_GROUPS: Array<{ group: string; options: Array<{ value: ModellingClass; label: string }> }> = [
  {
    group: "Bonds",
    options: [
      { value: "gvt_bond_fixed_coupon", label: "Government bond — fixed coupon" },
      { value: "gvt_bond_inflation_linked", label: "Government bond — inflation-linked" },
      { value: "corp_bond_fixed_coupon", label: "Corporate bond — fixed coupon" },
      { value: "corp_bond_floating_interest", label: "Corporate bond — floating rate" },
    ],
  },
  {
    group: "Swaps",
    options: [
      { value: "irs_fixed", label: "Interest rate swap — fixed leg" },
      { value: "irs_floating", label: "Interest rate swap — floating leg" },
      { value: "ils_fixed", label: "Inflation-linked swap — fixed leg" },
      { value: "ils_floating", label: "Inflation-linked swap — floating leg" },
    ],
  },
  {
    group: "Other",
    options: [
      { value: "fx_forward", label: "FX forward" },
      { value: "equity", label: "Equity" },
      { value: "cash", label: "Cash" },
    ],
  },
];

export const RATINGS = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"];
export const RATING_TO_CQS: Record<string, number> = { AAA: 0, AA: 1, A: 2, BBB: 3, BB: 4, B: 5, CCC: 6 };

export const BOND_CLASSES: ModellingClass[] = ["gvt_bond_fixed_coupon", "gvt_bond_inflation_linked", "corp_bond_fixed_coupon", "corp_bond_floating_interest"];
export const SWAP_CLASSES: ModellingClass[] = ["irs_fixed", "irs_floating", "ils_fixed", "ils_floating"];
export const INFLATION_CLASSES: ModellingClass[] = ["gvt_bond_inflation_linked", "ils_fixed", "ils_floating"];
export const FLOATING_CLASSES: ModellingClass[] = ["corp_bond_floating_interest", "irs_floating", "ils_floating"];
/** Which of `FLOATING_CLASSES` actually take a coupon spread over the floating
 * reference rate: `calc_bond_floating_interest` and `calc_irs_floating` both read
 * `annual_coupon_spread` with no fallback (backend/src/model/asset_risk/
 * asset_methods.py), so leaving it uncollected crashes the same way a missing
 * floating rate would. `ils_floating` is excluded -- its cashflow function
 * (`calc_ils_floating`) has no coupon stream at all (inflation-indexed redemption
 * only), so it never reads a spread. */
export const FLOATING_SPREAD_CLASSES: ModellingClass[] = ["corp_bond_floating_interest", "irs_floating"];
export const FIXED_RATE_CLASSES: ModellingClass[] = ["gvt_bond_fixed_coupon", "gvt_bond_inflation_linked", "corp_bond_fixed_coupon", "irs_fixed", "ils_fixed"];
export const RATED_CLASSES: ModellingClass[] = [...BOND_CLASSES];
/** `model_scr_spread_risk = 1` in `Model Parameters.xlsx`'s `modelling_properties`
 * sheet -- only these two classes actually run `Asset.calc_scr_spread_risk`
 * (government bonds are treated as risk-free, so `model_scr_spread_risk = 0` there).
 * That calc reads `modified_duration` straight off the asset with no fallback
 * (`max(1, modified_duration)` in `backend/src/model/asset_risk/asset_model.py`), so
 * it must be collected for these two classes specifically. */
export const SPREAD_RISK_CLASSES: ModellingClass[] = ["corp_bond_fixed_coupon", "corp_bond_floating_interest"];
/** `calc_ils_floating` (backend/src/model/asset_risk/asset_methods.py) reads
 * `inflation_index_start` with no fallback -- the inflation index level at swap
 * inception, used to build `indexation_coefficient = lagged_inflation_index /
 * inflation_index_start`. Unique to `ils_floating`: `gvt_bond_inflation_linked`
 * instead uses `current_indexation_coefficient` directly (see
 * `calc_bond_inflation_linked`), and `ils_fixed` has no inflation dependency at all
 * (its fixed leg settles at a flat agreed rate, `calc_ils_fixed`). */
export const INFLATION_INDEX_START_CLASSES: ModellingClass[] = ["ils_floating"];
