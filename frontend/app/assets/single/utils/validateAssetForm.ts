import type { FormState } from "./assetFormConstants";
import type { ModellingClassFlags } from "./modellingClassFlags";

export type AssetFormErrors = Partial<Record<keyof FormState, string>>;

const REQUIRED = "Required";

/** Which fields are required mirrors exactly which fields `AssetFormPanel` shows
 * for the selected class (same flags) -- a field hidden for this class was never
 * asked for, so it's never "missing". A blank numeric field is `""` (see
 * `FormState`'s docstring); dates/rating are required as non-empty strings. */
export function validateAssetForm(form: FormState, flags: ModellingClassFlags): AssetFormErrors {
  const {
    isBond,
    isSwap,
    hasInflation,
    isFloating,
    isFixedRate,
    isRated,
    isFxForward,
    isEquity,
    isCash,
    hasSpreadRisk,
    needsCouponSpread,
    needsInflationIndexStart,
  } = flags;
  const errors: AssetFormErrors = {};

  if (form.marketValue === "") errors.marketValue = REQUIRED;

  if (!isCash && !isEquity) {
    if (form.nominal === "") errors.nominal = REQUIRED;
    if (!form.issueDate) errors.issueDate = REQUIRED;
    if (!form.maturityDate) errors.maturityDate = REQUIRED;
  }

  if (isFxForward) {
    if (form.exchangeRate === "") errors.exchangeRate = REQUIRED;
    // `calc_fx_forwards` settles at `nominal_quotation_currency / exchange_rate` --
    // required with no fallback (backend/src/model/asset_risk/asset_methods.py).
    if (form.nominalQuotationCurrency === "") errors.nominalQuotationCurrency = REQUIRED;
  }

  if (isBond || isSwap) {
    if (!form.nextCouponDate) errors.nextCouponDate = REQUIRED;
  }

  if (isFixedRate || isFloating) {
    if (form.couponRate === "") errors.couponRate = REQUIRED;
  }
  if (needsCouponSpread && form.floatingSpread === "") errors.floatingSpread = REQUIRED;
  if (isSwap && form.swapTerm === "") errors.swapTerm = REQUIRED;

  if (hasInflation) {
    if (form.inflationIndexLag === "") errors.inflationIndexLag = REQUIRED;
    if (form.indexationCoefficient === "") errors.indexationCoefficient = REQUIRED;
  }

  // `calc_ils_floating` reads `inflation_index_start` with no fallback -- see
  // `INFLATION_INDEX_START_CLASSES`'s docstring for why this is `ils_floating` only.
  if (needsInflationIndexStart && form.inflationIndexStart === "") errors.inflationIndexStart = REQUIRED;

  if (isRated && !form.rating) errors.rating = REQUIRED;

  // `Asset.calc_scr_spread_risk` (backend/src/model/asset_risk/asset_model.py) reads
  // `modified_duration` straight off the asset with no fallback, for corporate bonds
  // only (`model_scr_spread_risk = 1` in Model Parameters.xlsx) -- government bonds
  // are risk-free so never model spread risk at all.
  if (hasSpreadRisk && form.modifiedDuration === "") errors.modifiedDuration = REQUIRED;

  return errors;
}
