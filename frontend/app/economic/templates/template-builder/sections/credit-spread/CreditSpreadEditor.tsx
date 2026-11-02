import { Button, IconButton, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";

import type { CqsMappingRow, SpreadCoefficientRow } from "@/lib/api/types";

export function CreditSpreadEditor({
  cqsMapping,
  spreadCoefficients,
  onChangeCqsMapping,
  onChangeSpreadCoefficients,
  locked = false,
}: {
  cqsMapping: CqsMappingRow[];
  spreadCoefficients: SpreadCoefficientRow[];
  onChangeCqsMapping: (rows: CqsMappingRow[]) => void;
  onChangeSpreadCoefficients: (rows: SpreadCoefficientRow[]) => void;
  /** Disables every field and hides add/remove controls -- used when the values come
   * from the Solvency II guideline (see CreditSpreadSection) rather than hand-entry. */
  locked?: boolean;
}) {
  function updateCqsRow(index: number, patch: Partial<CqsMappingRow>) {
    onChangeCqsMapping(cqsMapping.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  }
  function updateCoefficientRow(index: number, patch: Partial<SpreadCoefficientRow>) {
    onChangeSpreadCoefficients(spreadCoefficients.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  }

  return (
    <Stack spacing={3}>
      <Stack spacing={1.5}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="subtitle2">Credit quality step mapping</Typography>
          {!locked && (
            <Button
              size="small"
              startIcon={<AddIcon fontSize="small" />}
              onClick={() => onChangeCqsMapping([...cqsMapping, { rating: "", cqs: 0 }])}
            >
              Add rating
            </Button>
          )}
        </Stack>
        <Typography variant="body2" color="text.secondary">
          Map each rating bucket used by positions under this template to a CQS value from 0 to 6.
        </Typography>
        <Paper variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Rating</TableCell>
                <TableCell>CQS (0-6)</TableCell>
                {!locked && <TableCell align="right">Actions</TableCell>}
              </TableRow>
            </TableHead>
            <TableBody>
              {cqsMapping.map((row, idx) => (
                <TableRow key={idx} hover>
                  <TableCell>
                    <TextField
                      size="small"
                      value={row.rating}
                      onChange={(e) => updateCqsRow(idx, { rating: e.target.value })}
                      sx={{ maxWidth: 140 }}
                      slotProps={{ input: { readOnly: locked } }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="number"
                      value={row.cqs}
                      onChange={(e) => updateCqsRow(idx, { cqs: Number(e.target.value) })}
                      sx={{ maxWidth: 100 }}
                      slotProps={{ input: { readOnly: locked } }}
                    />
                  </TableCell>
                  {!locked && (
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => onChangeCqsMapping(cqsMapping.filter((_, i) => i !== idx))}>
                        <DeleteOutlineIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      </Stack>

      <Stack spacing={1.5}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="subtitle2">Spread risk coefficients</Typography>
          {!locked && (
            <Button
              size="small"
              startIcon={<AddIcon fontSize="small" />}
              onClick={() => onChangeSpreadCoefficients([...spreadCoefficients, { cqs: 0, duration_bucket: 0, a: 0, b: 0 }])}
            >
              Add coefficient
            </Button>
          )}
        </Stack>
        <Typography variant="body2" color="text.secondary">
          Coefficients by CQS and duration bucket, applied to spread-risk-bearing modelling classes during
          aggregation.
        </Typography>
        <Paper variant="outlined" sx={{ overflowX: "auto" }}>
          <Table size="small" sx={{ minWidth: 520 }}>
            <TableHead>
              <TableRow>
                <TableCell>CQS</TableCell>
                <TableCell>Duration bucket</TableCell>
                <TableCell>Coefficient a</TableCell>
                <TableCell>Coefficient b</TableCell>
                {!locked && <TableCell align="right">Actions</TableCell>}
              </TableRow>
            </TableHead>
            <TableBody>
              {spreadCoefficients.map((row, idx) => (
                <TableRow key={idx} hover>
                  <TableCell>
                    <TextField
                      size="small"
                      type="number"
                      value={row.cqs}
                      onChange={(e) => updateCoefficientRow(idx, { cqs: Number(e.target.value) })}
                      sx={{ maxWidth: 90 }}
                      slotProps={{ input: { readOnly: locked } }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="number"
                      value={row.duration_bucket}
                      onChange={(e) => updateCoefficientRow(idx, { duration_bucket: Number(e.target.value) })}
                      sx={{ maxWidth: 130 }}
                      slotProps={{ input: { readOnly: locked } }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="number"
                      value={row.a}
                      onChange={(e) => updateCoefficientRow(idx, { a: Number(e.target.value) })}
                      sx={{ maxWidth: 110 }}
                      slotProps={{ input: { readOnly: locked } }}
                    />
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      type="number"
                      value={row.b}
                      onChange={(e) => updateCoefficientRow(idx, { b: Number(e.target.value) })}
                      sx={{ maxWidth: 110 }}
                      slotProps={{ input: { readOnly: locked } }}
                    />
                  </TableCell>
                  {!locked && (
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => onChangeSpreadCoefficients(spreadCoefficients.filter((_, i) => i !== idx))}>
                        <DeleteOutlineIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      </Stack>
    </Stack>
  );
}
