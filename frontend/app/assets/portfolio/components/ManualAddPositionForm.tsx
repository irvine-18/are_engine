import { useState } from "react";
import { Alert, Box, Button, Stack, TextField } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";

import { AssetPropertyFields } from "@/app/assets/single/components/AssetPropertyFields";
import { DEFAULT_FORM, type FormState } from "@/app/assets/single/utils/assetFormConstants";
import { getModellingClassFlags } from "@/app/assets/single/utils/modellingClassFlags";
import { validateAssetForm } from "@/app/assets/single/utils/validateAssetForm";
import { buildPositionCreate } from "../utils/buildPositionCreate";
import type { PositionCreate } from "@/lib/api/types";

interface ManualAddPositionFormProps {
  currency: string;
  onAdd: (input: PositionCreate) => void;
  isAdding: boolean;
}

/** The same per-modelling-class fields as Single Asset (`AssetPropertyFields`),
 * so adding a position here requires exactly what that class needs to be priced --
 * not the smaller fixed field set the old "Add single asset" drawer collected. */
export function ManualAddPositionForm({ currency, onAdd, isAdding }: ManualAddPositionFormProps) {
  const [name, setName] = useState("");
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);

  const flags = getModellingClassFlags(form);
  const errors = validateAssetForm(form, flags);
  const hasErrors = Object.keys(errors).length > 0;
  const canAdd = name.trim().length > 0 && !hasErrors;

  function handleAdd() {
    if (!canAdd) return;
    onAdd(buildPositionCreate(name.trim(), form, currency, flags));
    setName("");
    setForm(DEFAULT_FORM);
  }

  return (
    <Stack spacing={2} sx={{ maxWidth: 560 }}>
      <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} helperText="Required" />
      <AssetPropertyFields form={form} onChange={setForm} flags={flags} errors={errors} />
      <Box>
        <Button variant="contained" startIcon={<AddIcon />} disabled={!canAdd || isAdding} onClick={handleAdd}>
          {isAdding ? "Adding…" : "Add position"}
        </Button>
      </Box>
      {hasErrors && (
        <Alert severity="warning">Fill in every required field (highlighted above) before adding.</Alert>
      )}
    </Stack>
  );
}
