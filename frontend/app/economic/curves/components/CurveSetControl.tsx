import { MenuItem, Stack, TextField } from "@mui/material";

import { CURVE_SETS } from "../utils/curveRunRequest";
import type { CurveSet } from "@/lib/api/types";

interface CurveSetControlProps {
  curveSet: CurveSet;
  onCurveSetChange: (curveSet: CurveSet) => void;
}

export function CurveSetControl({ curveSet, onCurveSetChange }: CurveSetControlProps) {
  return (
    <Stack direction="row" spacing={2}>
      <TextField select label="Curve set" value={curveSet} onChange={(e) => onCurveSetChange(e.target.value as CurveSet)} sx={{ minWidth: 200 }}>
        {CURVE_SETS.map((cs) => (
          <MenuItem key={cs} value={cs}>
            {cs}
          </MenuItem>
        ))}
      </TextField>
    </Stack>
  );
}
