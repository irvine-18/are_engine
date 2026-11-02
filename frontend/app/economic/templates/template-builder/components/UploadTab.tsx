"use client";

import { useState } from "react";
import { Alert, Box, Button, Paper, Stack, Typography } from "@mui/material";
import InsertDriveFileOutlinedIcon from "@mui/icons-material/InsertDriveFileOutlined";
import * as XLSX from "xlsx";

import { FileDropzone } from "@/components/inputs/FileDropzone";
import type { LiquidRatePoint } from "@/lib/api/types";

/** The file's rate column is read as a percentage (2.10 = 2.10%) to match how rates are
 * entered in the manual grid; `LiquidRatePoint.rate` itself stays a decimal. Parsed points
 * go straight into the manual grid above -- there's no separate preview table here. */
const REQUIRED_COLUMNS = ["tenor", "rate", "liquid"] as const;

function parseLiquidFlag(value: unknown): boolean {
  if (typeof value === "boolean") return value;
  const normalized = String(value).trim().toLowerCase();
  return normalized === "true" || normalized === "1" || normalized === "yes" || normalized === "y";
}

function formatFileSize(bytes: number) {
  return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(0)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadTab({ onParsed }: { onParsed: (points: LiquidRatePoint[]) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);

  const changeFile = () => {
    setFile(null);
    setError(null);
    setSuccess(null);
  };

  const processFile = async () => {
    if (!file) return;
    setProcessing(true);
    setError(null);
    setSuccess(null);
    try {
      const buffer = await file.arrayBuffer();
      const workbook = XLSX.read(buffer, { type: "array" });
      const sheet = workbook.Sheets[workbook.SheetNames[0]];
      const rows: Record<string, unknown>[] = XLSX.utils.sheet_to_json(sheet);

      if (rows.length === 0) {
        setError("The file has no data rows.");
        return;
      }

      const columnByKey = new Map(Object.keys(rows[0]).map((c) => [c.trim().toLowerCase(), c]));
      const missing = REQUIRED_COLUMNS.filter((c) => !columnByKey.has(c));
      if (missing.length > 0) {
        setError(`Missing required column${missing.length === 1 ? "" : "s"}: ${missing.join(", ")}. Columns must be named tenor, rate and liquid.`);
        return;
      }

      const tenorCol = columnByKey.get("tenor")!;
      const rateCol = columnByKey.get("rate")!;
      const liquidCol = columnByKey.get("liquid")!;

      const points: LiquidRatePoint[] = rows
        .map((row) => ({
          tenor_years: Number(row[tenorCol]),
          rate: Number(row[rateCol]) / 100,
          liquid: parseLiquidFlag(row[liquidCol]),
          source: "upload",
        }))
        .filter((p) => Number.isFinite(p.tenor_years) && Number.isFinite(p.rate));

      if (points.length === 0) {
        setError("Couldn't read any valid tenor/rate rows from this file.");
        return;
      }

      const tenors = points.map((p) => p.tenor_years);
      const duplicateTenors = [...new Set(tenors.filter((t, i) => tenors.indexOf(t) !== i))];
      if (duplicateTenors.length > 0) {
        setError(`Duplicate tenor${duplicateTenors.length === 1 ? "" : "s"} found: ${duplicateTenors.join(", ")}. Each tenor must appear once.`);
        return;
      }

      onParsed(points);
      setSuccess(`Processed successfully — ${points.length} point${points.length === 1 ? "" : "s"} applied to the grid.`);
    } finally {
      setProcessing(false);
    }
  };

  const downloadSample = () => {
    const csv =
      "tenor,rate,liquid\n" +
      "1,2.10,TRUE\n" +
      "2,2.18,TRUE\n" +
      "3,2.24,TRUE\n" +
      "5,2.35,TRUE\n" +
      "10,2.60,TRUE\n" +
      "15,2.68,TRUE\n" +
      "20,2.75,TRUE\n" +
      "30,2.80,FALSE\n" +
      "50,2.72,FALSE\n";
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "swap_rates_sample.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Stack spacing={2}>
      {file ? (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <InsertDriveFileOutlinedIcon color="action" />
            <Box sx={{ minWidth: 0, flexGrow: 1 }}>
              <Typography variant="body2" fontWeight={500} noWrap title={file.name}>
                {file.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatFileSize(file.size)}
              </Typography>
            </Box>
            <Button size="small" onClick={changeFile} disabled={processing}>
              Change file
            </Button>
            <Button size="small" variant="contained" onClick={processFile} disabled={processing}>
              {processing ? "Processing…" : "Process file"}
            </Button>
          </Stack>
        </Paper>
      ) : (
        <FileDropzone
          onFile={(f) => {
            setFile(f);
            setError(null);
            setSuccess(null);
          }}
        />
      )}

      {error && <Alert severity="error">{error}</Alert>}
      {success && <Alert severity="success">{success}</Alert>}

      <Stack direction="row" spacing={1.5} alignItems="center">
        <Button size="small" onClick={downloadSample} sx={{ alignSelf: "flex-start" }}>
          Download sample file
        </Button>
        <Typography variant="caption" color="text.secondary">
          Columns required: <strong>tenor</strong> (years), <strong>rate</strong> (%), <strong>liquid</strong> (TRUE/FALSE)
        </Typography>
      </Stack>
    </Stack>
  );
}
