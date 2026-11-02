import { Alert, Button, LinearProgress, MenuItem, Stack, TextField, Typography } from "@mui/material";

import { AssetPropertyFields } from "./AssetPropertyFields";
import type { FormState } from "../utils/assetFormConstants";
import type { ModellingClassFlags } from "../utils/modellingClassFlags";
import type { AssetFormErrors } from "../utils/validateAssetForm";
import type { SampleAsset } from "@/lib/api/types";

interface AssetFormPanelProps {
  form: FormState;
  onChange: (form: FormState) => void;
  flags: ModellingClassFlags;
  /** Field -> message, only for fields required by the selected class (see
   * `validateAssetForm.ts`). Drives each field's `error`/`helperText` and blocks
   * Calculate until empty. */
  errors: AssetFormErrors;
  /** One prepared asset per modelling class (`useSampleAssets`), fetched once when
   * Single Asset mounts. Picking one overwrites every form field, including the
   * modelling class itself. */
  samples: SampleAsset[];
  onLoadSample: (sample: SampleAsset) => void;
  onCalculate: () => void;
  /** False when the active template has no curve run to price against yet -- see
   * `SingleAssetPage`'s own warning Alert for the explanation shown above the form. */
  canCalculate: boolean;
  isCalculating: boolean;
  calculateError: Error | null;
}

export function AssetFormPanel({
  form,
  onChange,
  flags,
  errors,
  samples,
  onLoadSample,
  onCalculate,
  canCalculate,
  isCalculating,
  calculateError,
}: AssetFormPanelProps) {
  const hasErrors = Object.keys(errors).length > 0;

  return (
    <Stack spacing={2}>
      {samples.length > 0 && (
        <TextField
          select
          label="Load sample asset"
          value=""
          onChange={(e) => {
            const sample = samples.find((s) => s.id === e.target.value);
            if (sample) onLoadSample(sample);
          }}
          helperText="Optional — fills in every field with a realistic starting point for a class."
        >
          {samples.map((s) => (
            <MenuItem key={s.id} value={s.id}>
              {s.name}
            </MenuItem>
          ))}
        </TextField>
      )}

      <AssetPropertyFields form={form} onChange={onChange} flags={flags} errors={errors} />

      <Button variant="contained" onClick={onCalculate} disabled={isCalculating || !canCalculate || hasErrors}>
        Calculate
      </Button>
      {hasErrors && !isCalculating && (
        <Alert severity="warning">Fill in every required field (highlighted above) before calculating.</Alert>
      )}
      {isCalculating && (
        <Stack spacing={0.5}>
          <LinearProgress sx={{ borderRadius: 1 }} />
          <Typography variant="caption" color="text.secondary">
            Pricing against the active template's curves…
          </Typography>
        </Stack>
      )}
      {calculateError && <Alert severity="error">{calculateError.message}</Alert>}
    </Stack>
  );
}
