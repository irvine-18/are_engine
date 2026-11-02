import { buildAssetInput, num } from "@/app/assets/single/utils/buildAssetInput";
import type { FormState } from "@/app/assets/single/utils/assetFormConstants";
import type { ModellingClassFlags } from "@/app/assets/single/utils/modellingClassFlags";
import type { PositionCreate } from "@/lib/api/types";

/** Shared by the portfolio "Manually Add Positions" form and Single Asset's "Add to
 * portfolio" dialog -- both collect a `FormState` the same way (see
 * `AssetPropertyFields`), so both build the same `PositionCreate` payload, including
 * the full `asset_detail` (not just the Positions grid's summary fields). */
export function buildPositionCreate(name: string, form: FormState, currency: string, flags: ModellingClassFlags): PositionCreate {
  return {
    name,
    modelling_class: form.modellingClass,
    rating: flags.isRated ? form.rating : null,
    nominal: flags.isCash || flags.isEquity ? null : num(form.nominal),
    market_value: num(form.marketValue),
    maturity_date: flags.isCash || flags.isEquity ? null : form.maturityDate || null,
    currency,
    asset_detail: buildAssetInput(form, currency, flags),
  };
}
