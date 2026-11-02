import { MenuItem, TextField } from "@mui/material";

import { MODELLING_CLASS_GROUPS, RATINGS, type FormState } from "../utils/assetFormConstants";
import type { ModellingClassFlags } from "../utils/modellingClassFlags";
import type { AssetFormErrors } from "../utils/validateAssetForm";
import type { ModellingClass } from "@/lib/api/types";

interface AssetPropertyFieldsProps {
  form: FormState;
  onChange: (form: FormState) => void;
  flags: ModellingClassFlags;
  /** Field -> message, only for fields required by the selected class (see
   * `validateAssetForm.ts`). Drives each field's `error`/`helperText`. */
  errors: AssetFormErrors;
}

/** Every `FormState` field, shown or hidden per the selected modelling class (see
 * `flags`) -- shared between Single Asset's `AssetFormPanel` (adds a sample picker
 * and Calculate button around this) and the portfolio "Manually Add Positions" form
 * (adds a Name field and an Add button instead), so both collect identical,
 * class-correct fields for the engine. */
export function AssetPropertyFields({ form, onChange, flags, errors }: AssetPropertyFieldsProps) {
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
    cqs,
  } = flags;

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => onChange({ ...form, [key]: value });
  const setNumber = <K extends keyof FormState>(key: K, raw: string) => set(key, (raw === "" ? "" : Number(raw)) as FormState[K]);

  return (
    <>
      <TextField select label="Modelling class" value={form.modellingClass} onChange={(e) => set("modellingClass", e.target.value as ModellingClass)}>
        {MODELLING_CLASS_GROUPS.flatMap((g) => [
          <MenuItem key={g.group} disabled divider sx={{ opacity: 0.7, fontSize: "0.7rem", textTransform: "uppercase" }}>
            {g.group}
          </MenuItem>,
          ...g.options.map((o) => (
            <MenuItem key={o.value} value={o.value}>
              {o.label}
            </MenuItem>
          )),
        ])}
      </TextField>

      {!isCash && !isEquity && (
        <TextField
          label="Nominal"
          type="number"
          value={form.nominal}
          onChange={(e) => setNumber("nominal", e.target.value)}
          error={Boolean(errors.nominal)}
          helperText={errors.nominal}
        />
      )}
      <TextField
        label="Market value"
        type="number"
        value={form.marketValue}
        onChange={(e) => setNumber("marketValue", e.target.value)}
        error={Boolean(errors.marketValue)}
        helperText={errors.marketValue}
      />

      {isFxForward && (
        <>
          <TextField
            label="Exchange rate"
            type="number"
            value={form.exchangeRate}
            onChange={(e) => setNumber("exchangeRate", e.target.value)}
            error={Boolean(errors.exchangeRate)}
            helperText={errors.exchangeRate}
          />
          <TextField
            label="Notional (quotation currency)"
            type="number"
            value={form.nominalQuotationCurrency}
            onChange={(e) => setNumber("nominalQuotationCurrency", e.target.value)}
            error={Boolean(errors.nominalQuotationCurrency)}
            helperText={errors.nominalQuotationCurrency ?? "Settles as this ÷ exchange rate -- drives the forward's payoff."}
          />
        </>
      )}

      {!isCash && !isEquity && (
        <TextField
          label="Issue date"
          type="date"
          value={form.issueDate}
          onChange={(e) => set("issueDate", e.target.value)}
          InputLabelProps={{ shrink: true }}
          error={Boolean(errors.issueDate)}
          helperText={errors.issueDate}
        />
      )}
      {!isCash && !isEquity && (
        <TextField
          label="Maturity date"
          type="date"
          value={form.maturityDate}
          onChange={(e) => set("maturityDate", e.target.value)}
          InputLabelProps={{ shrink: true }}
          error={Boolean(errors.maturityDate)}
          helperText={errors.maturityDate}
        />
      )}

      {(isBond || isSwap) && (
        <>
          <TextField
            label="Next coupon date"
            type="date"
            value={form.nextCouponDate}
            onChange={(e) => set("nextCouponDate", e.target.value)}
            InputLabelProps={{ shrink: true }}
            error={Boolean(errors.nextCouponDate)}
            helperText={errors.nextCouponDate}
          />
          <TextField select label="Coupon frequency" value={form.couponFrequency} onChange={(e) => set("couponFrequency", Number(e.target.value))}>
            <MenuItem value={1}>Annual</MenuItem>
            <MenuItem value={2}>Semi-annual</MenuItem>
            <MenuItem value={4}>Quarterly</MenuItem>
          </TextField>
        </>
      )}

      {isFixedRate && (
        <TextField
          label={isSwap ? "Fixed interest rate (%)" : "Annual fixed coupon rate (%)"}
          type="number"
          value={form.couponRate}
          onChange={(e) => setNumber("couponRate", e.target.value)}
          error={Boolean(errors.couponRate)}
          helperText={errors.couponRate}
        />
      )}
      {isFloating && (
        <>
          <TextField
            label={isSwap ? "Floating interest rate (%)" : "Floating coupon rate (%)"}
            type="number"
            value={form.couponRate}
            onChange={(e) => setNumber("couponRate", e.target.value)}
            error={Boolean(errors.couponRate)}
            helperText={errors.couponRate}
          />
          {needsCouponSpread && (
            <TextField
              label="Coupon spread (bp)"
              type="number"
              value={form.floatingSpread}
              onChange={(e) => setNumber("floatingSpread", e.target.value)}
              error={Boolean(errors.floatingSpread)}
              helperText={errors.floatingSpread}
            />
          )}
        </>
      )}
      {isSwap && (
        <TextField
          label="Swap term (years)"
          type="number"
          value={form.swapTerm}
          onChange={(e) => setNumber("swapTerm", e.target.value)}
          error={Boolean(errors.swapTerm)}
          helperText={errors.swapTerm}
        />
      )}

      {hasInflation && (
        <>
          <TextField
            label="Inflation index lag (months)"
            type="number"
            value={form.inflationIndexLag}
            onChange={(e) => setNumber("inflationIndexLag", e.target.value)}
            error={Boolean(errors.inflationIndexLag)}
            helperText={errors.inflationIndexLag}
          />
          <TextField
            label="Current indexation coefficient"
            type="number"
            value={form.indexationCoefficient}
            onChange={(e) => setNumber("indexationCoefficient", e.target.value)}
            error={Boolean(errors.indexationCoefficient)}
            helperText={errors.indexationCoefficient}
          />
        </>
      )}

      {needsInflationIndexStart && (
        <TextField
          label="Inflation index start"
          type="number"
          value={form.inflationIndexStart}
          onChange={(e) => setNumber("inflationIndexStart", e.target.value)}
          error={Boolean(errors.inflationIndexStart)}
          helperText={errors.inflationIndexStart ?? "Inflation index level at swap inception."}
        />
      )}

      {isEquity && (
        <TextField select label="Equity type" value={form.equityType} onChange={(e) => set("equityType", Number(e.target.value))}>
          <MenuItem value={1}>Type 1</MenuItem>
          <MenuItem value={2}>Type 2</MenuItem>
        </TextField>
      )}

      {isRated && (
        <TextField
          select
          label="Rating"
          value={form.rating}
          onChange={(e) => set("rating", e.target.value)}
          error={Boolean(errors.rating)}
          helperText={errors.rating ?? (cqs !== null ? `CQS ${cqs}` : undefined)}
        >
          {RATINGS.map((r) => (
            <MenuItem key={r} value={r}>
              {r}
            </MenuItem>
          ))}
        </TextField>
      )}

      {hasSpreadRisk && (
        <TextField
          label="Modified duration (years)"
          type="number"
          value={form.modifiedDuration}
          onChange={(e) => setNumber("modifiedDuration", e.target.value)}
          error={Boolean(errors.modifiedDuration)}
          helperText={errors.modifiedDuration ?? "Used for SCR spread risk — corporate bonds only."}
        />
      )}
    </>
  );
}
