import {
  BOND_CLASSES,
  FIXED_RATE_CLASSES,
  FLOATING_CLASSES,
  FLOATING_SPREAD_CLASSES,
  INFLATION_CLASSES,
  INFLATION_INDEX_START_CLASSES,
  RATED_CLASSES,
  RATING_TO_CQS,
  SPREAD_RISK_CLASSES,
  SWAP_CLASSES,
  type FormState,
} from "./assetFormConstants";

export interface ModellingClassFlags {
  isBond: boolean;
  isSwap: boolean;
  hasInflation: boolean;
  isFloating: boolean;
  isFixedRate: boolean;
  isRated: boolean;
  isFxForward: boolean;
  isEquity: boolean;
  isCash: boolean;
  hasSpreadRisk: boolean;
  needsCouponSpread: boolean;
  needsInflationIndexStart: boolean;
  cqs: number | null;
}

export function getModellingClassFlags(form: FormState): ModellingClassFlags {
  const isBond = BOND_CLASSES.includes(form.modellingClass);
  const isSwap = SWAP_CLASSES.includes(form.modellingClass);
  const hasInflation = INFLATION_CLASSES.includes(form.modellingClass);
  const isFloating = FLOATING_CLASSES.includes(form.modellingClass);
  const isFixedRate = FIXED_RATE_CLASSES.includes(form.modellingClass);
  const isRated = RATED_CLASSES.includes(form.modellingClass);
  const isFxForward = form.modellingClass === "fx_forward";
  const isEquity = form.modellingClass === "equity";
  const isCash = form.modellingClass === "cash";
  const hasSpreadRisk = SPREAD_RISK_CLASSES.includes(form.modellingClass);
  const needsCouponSpread = FLOATING_SPREAD_CLASSES.includes(form.modellingClass);
  const needsInflationIndexStart = INFLATION_INDEX_START_CLASSES.includes(form.modellingClass);
  const cqs = isRated ? RATING_TO_CQS[form.rating] ?? null : null;

  return {
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
    cqs,
  };
}
