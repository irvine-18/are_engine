import { BOND_CLASSES, type FormState } from "./assetFormConstants";
import type { ModellingClassFlags } from "./modellingClassFlags";
import type { AssetPropertiesInput } from "@/lib/api/types";

/** A blank (`""`) required field only ever reaches here while `canCalculate` is
 * false (see `validateAssetForm.ts`/`SingleAssetPage`'s `Calculate` button) -- this
 * payload is never actually sent in that state, so `0` is just a safe, typed
 * placeholder for the preview `asset` built on every keystroke. */
export const num = (v: number | ""): number => (v === "" ? 0 : v);

export function buildAssetInput(form: FormState, currency: string, flags: ModellingClassFlags): AssetPropertiesInput {
  const {
    isBond,
    isSwap,
    hasInflation,
    isFloating,
    isFixedRate,
    isRated,
    isFxForward,
    isCash,
    isEquity,
    hasSpreadRisk,
    needsCouponSpread,
    needsInflationIndexStart,
  } = flags;

  return {
    position_id: "SINGLE_ASSET_PREVIEW",
    portfolio: "SINGLE",
    asset_id: "PREVIEW",
    modelling_class: form.modellingClass,
    quotation_currency: currency,
    exchange_rate: num(form.exchangeRate),
    market_value: num(form.marketValue),
    nominal: isCash || isEquity ? null : num(form.nominal),
    rating: isRated ? form.rating : null,
    modified_duration: hasSpreadRisk ? num(form.modifiedDuration) : null,
    issue_date: form.issueDate || null,
    maturity_date: isCash || isEquity ? null : form.maturityDate || null,
    next_coupon_date: isBond || isSwap ? form.nextCouponDate || null : null,
    coupon_frequency: isBond || isSwap ? form.couponFrequency : null,
    // `gvt_bond_inflation_linked` is a `FIXED_RATE_CLASSES` bond too, but its cashflow
    // function (`calc_bond_inflation_linked`, backend/src/model/asset_risk/
    // asset_methods.py) reads `annual_nominal_coupon_rate`, not
    // `annual_fixed_coupon_rate` (that name is `calc_bond_fixed_coupon`'s own param) --
    // sending the wrong one left the right one `None`, crashing on `rate / coupon_frequency`.
    annual_fixed_coupon_rate:
      BOND_CLASSES.includes(form.modellingClass) && isFixedRate && form.modellingClass !== "gvt_bond_inflation_linked"
        ? num(form.couponRate) / 100
        : null,
    annual_nominal_coupon_rate: form.modellingClass === "gvt_bond_inflation_linked" ? num(form.couponRate) / 100 : null,
    annual_floating_coupon_rate: form.modellingClass === "corp_bond_floating_interest" ? num(form.couponRate) / 100 : null,
    // `irs_floating` reads this too (`calc_irs_floating`), not just non-swap floaters
    // -- `ils_floating` is the only `isFloating` class that doesn't (see
    // `FLOATING_SPREAD_CLASSES`'s docstring).
    annual_coupon_spread: needsCouponSpread ? num(form.floatingSpread) / 100 : null,
    annual_fixed_interest_rate: isSwap && isFixedRate ? num(form.couponRate) / 100 : null,
    annual_floating_interest_rate: isSwap && isFloating ? num(form.couponRate) / 100 : null,
    swap_term: isSwap ? num(form.swapTerm) : null,
    // Must be the asset_rates_table's literal column name, not a display label --
    // `calc_ils_floating` reads it as `df_cashflow_matrix[inflation_index]`
    // (backend/src/model/asset_risk/asset_model.py's `calc_cashflows` passes this
    // value straight through as the column to look up). The table only ever has
    // "hicp"/"hicp01" (see `services/economic_service.py::build_asset_rates_table`);
    // "HICPxT" is a cosmetic index-name label used elsewhere in the UI
    // (`InflationIndexBanner`) and was wrongly reused here, causing `KeyError:
    // 'HICPxT'` for `ils_floating` specifically (the only class that actually reads
    // this field as a column lookup -- `calc_bond_inflation_linked`/`calc_ils_fixed`
    // ignore it).
    inflation_index: hasInflation ? "hicp" : null,
    inflation_index_lag: hasInflation ? num(form.inflationIndexLag) : null,
    current_indexation_coefficient: hasInflation ? num(form.indexationCoefficient) : null,
    // `calc_ils_floating` reads this with no fallback -- see
    // `INFLATION_INDEX_START_CLASSES`'s docstring for why only `ils_floating` needs it.
    inflation_index_start: needsInflationIndexStart ? num(form.inflationIndexStart) : null,
    equity_type: isEquity ? form.equityType : null,
    // `calc_fx_forwards` reads all three with no fallback. `nominal` doubles as the
    // portfolio-currency leg (the function overwrites the matrix's own "nominal"
    // column with `nominal_portfolio_currency` anyway); `nominal_quotation_currency`
    // is the one that actually drives the payoff (`.../exchange_rate`), so it needs
    // its own field (`form.nominalQuotationCurrency`), not derived from `nominal`.
    // `annual_interest_rate` feeds a `coupon_payment` that's computed then
    // immediately overwritten to `0` right after (dead code in `calc_fx_forwards`),
    // so `0` here is provably equivalent to any other value -- no UI field needed.
    nominal_portfolio_currency: isFxForward ? num(form.nominal) : null,
    nominal_quotation_currency: isFxForward ? num(form.nominalQuotationCurrency) : null,
    annual_interest_rate: isFxForward ? 0 : null,
  };
}
