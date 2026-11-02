import { DEFAULT_FORM, type FormState } from "./assetFormConstants";
import type { AssetPropertiesInput } from "@/lib/api/types";

/** Inverse of `buildAssetInput.ts`: turns a prepared sample (or any other
 * `AssetPropertiesInput`) back into form fields for the "Load sample" picker.
 * Only populates the fields relevant to `asset.modelling_class` -- everything else
 * falls back to `DEFAULT_FORM` since `AssetFormPanel` only ever shows the fields
 * relevant to the selected class anyway, so a stale default there is never seen. */
export function formFromAssetInput(asset: AssetPropertiesInput): FormState {
  // Whichever one of these the engine actually used (see `buildAssetInput.ts`'s own
  // four mutually-exclusive rate fields, one per bond/swap x fixed/floating combo).
  const couponRate =
    asset.annual_fixed_coupon_rate ??
    asset.annual_nominal_coupon_rate ??
    asset.annual_floating_coupon_rate ??
    asset.annual_fixed_interest_rate ??
    asset.annual_floating_interest_rate ??
    null;

  return {
    modellingClass: asset.modelling_class,
    nominal: asset.nominal ?? DEFAULT_FORM.nominal,
    marketValue: asset.market_value,
    issueDate: asset.issue_date ?? DEFAULT_FORM.issueDate,
    maturityDate: asset.maturity_date ?? DEFAULT_FORM.maturityDate,
    nextCouponDate: asset.next_coupon_date ?? DEFAULT_FORM.nextCouponDate,
    couponFrequency: asset.coupon_frequency ?? DEFAULT_FORM.couponFrequency,
    couponRate: couponRate !== null ? couponRate * 100 : DEFAULT_FORM.couponRate,
    floatingSpread: asset.annual_coupon_spread != null ? asset.annual_coupon_spread * 100 : DEFAULT_FORM.floatingSpread,
    swapTerm: asset.swap_term ?? DEFAULT_FORM.swapTerm,
    inflationIndexLag: asset.inflation_index_lag ?? DEFAULT_FORM.inflationIndexLag,
    indexationCoefficient: asset.current_indexation_coefficient ?? DEFAULT_FORM.indexationCoefficient,
    inflationIndexStart: asset.inflation_index_start ?? DEFAULT_FORM.inflationIndexStart,
    exchangeRate: asset.exchange_rate ?? DEFAULT_FORM.exchangeRate,
    nominalQuotationCurrency: asset.nominal_quotation_currency ?? DEFAULT_FORM.nominalQuotationCurrency,
    equityType: asset.equity_type ?? DEFAULT_FORM.equityType,
    rating: asset.rating ?? DEFAULT_FORM.rating,
    modifiedDuration: asset.modified_duration ?? DEFAULT_FORM.modifiedDuration,
  };
}
