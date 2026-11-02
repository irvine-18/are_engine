import { useState } from "react";
import { Alert, Box, Button, Chip, FormControlLabel, LinearProgress, Paper, Radio, RadioGroup, Stack, Typography } from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import UploadIcon from "@mui/icons-material/Upload";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";

import { FileDropzone } from "@/components/inputs/FileDropzone";
import { DataTable } from "@/components/data/DataTable";
import { useEconomicTemplates } from "@/stores/economicTemplates";
import { useAddPosition, useUploadTpt } from "@/lib/api/hooks";
import { DEFAULT_CURRENCY, defaultValuationDate } from "@/lib/economicTemplates";
import { downloadSamplePortfolio } from "../utils/positionsFileExports";
import { ManualAddPositionForm } from "./ManualAddPositionForm";
import type { ValidationIssue } from "@/lib/api/types";

type UploadMode = "file" | "manual";

interface UploadedFile {
  name: string;
  positionsImported: number;
}

/** No wizard steps -- picking "Upload Positions File" validates and imports (see
 * `services/portfolio_service.py::parse_positions_file`) in one click, replacing
 * whatever positions the portfolio already had (not appending to them). The
 * current positions list (`PositionsList`, rendered by `PortfolioDetailView`
 * directly below this panel) reflects that replacement as soon as the upload --
 * or a manual add -- succeeds. */
export function UploadPositionsPanel({
  portfolioId,
  onImported,
  onAdded,
}: {
  portfolioId: string;
  onImported: (count: number) => void;
  onAdded: () => void;
}) {
  const [mode, setMode] = useState<UploadMode>("file");
  const [file, setFile] = useState<File | null>(null);
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const [issues, setIssues] = useState<ValidationIssue[] | null>(null);

  const { activeTemplate } = useEconomicTemplates();
  const currency = activeTemplate?.currency ?? DEFAULT_CURRENCY;
  const valuationDate = activeTemplate?.valuationDate ?? defaultValuationDate();

  const uploadTpt = useUploadTpt(portfolioId);
  const addPosition = useAddPosition(portfolioId);

  const errorCount = issues?.filter((i) => i.severity === "error").length ?? 0;
  const warningCount = issues?.filter((i) => i.severity === "warning").length ?? 0;

  function handleUpload() {
    if (!file) return;
    const uploadedName = file.name;
    uploadTpt.mutate(
      { file, valuationDate },
      {
        onSuccess: (result) => {
          setIssues(result.validation_issues);
          if (result.positions_imported > 0) {
            setUploadedFile({ name: uploadedName, positionsImported: result.positions_imported });
            setFile(null);
            onImported(result.positions_imported);
          }
        },
      },
    );
  }

  function handleReplaceFile() {
    setUploadedFile(null);
    setFile(null);
    setIssues(null);
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Upload Positions
      </Typography>

      <RadioGroup
        row
        value={mode}
        onChange={(e) => {
          setMode(e.target.value as UploadMode);
          setIssues(null);
        }}
        sx={{ mb: 3 }}
      >
        <FormControlLabel value="file" control={<Radio />} label="Upload Positions File" />
        <FormControlLabel value="manual" control={<Radio />} label="Manually Add Positions" />
      </RadioGroup>

      {mode === "file" ? (
        <Stack spacing={2} sx={{ maxWidth: 560 }}>
          {uploadedFile ? (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <CheckCircleOutlineIcon color="success" />
                <Stack sx={{ minWidth: 0, flex: 1 }}>
                  <Typography variant="body2" noWrap>
                    {uploadedFile.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {uploadedFile.positionsImported} position(s) imported — replaced the previous list
                  </Typography>
                </Stack>
                <Button size="small" onClick={handleReplaceFile}>
                  Replace file
                </Button>
              </Stack>
            </Paper>
          ) : (
            <FileDropzone
              accept=".xlsx,.csv"
              onFile={(f) => {
                setFile(f);
                setIssues(null);
              }}
            />
          )}

          <Box>
            <Button size="small" variant="outlined" startIcon={<DownloadIcon />} onClick={downloadSamplePortfolio}>
              Download sample portfolio
            </Button>
          </Box>

          {!uploadedFile && (
            <Box>
              <Button variant="contained" startIcon={<UploadIcon />} disabled={!file || uploadTpt.isPending} onClick={handleUpload}>
                {uploadTpt.isPending ? "Uploading…" : "Upload"}
              </Button>
            </Box>
          )}

          {uploadTpt.isPending && <LinearProgress sx={{ borderRadius: 1 }} />}
          {uploadTpt.isError && <Alert severity="error">{(uploadTpt.error as Error).message}</Alert>}
        </Stack>
      ) : (
        <ManualAddPositionForm
          currency={currency}
          isAdding={addPosition.isPending}
          onAdd={(input) => {
            addPosition.mutate(input, { onSuccess: () => onAdded() });
          }}
        />
      )}

      {issues && issues.length > 0 && (
        <Stack spacing={1.5} sx={{ mt: 3, maxWidth: 820 }}>
          {errorCount > 0 ? (
            <Alert severity="error">{errorCount} error(s) found — nothing was imported. Fix the file below and upload again.</Alert>
          ) : (
            <Alert severity="success">Imported with {warningCount} warning(s) — see the log below.</Alert>
          )}
          <Typography variant="subtitle2">Validation log</Typography>
          <DataTable
            height={280}
            fileName="validation-log"
            rows={issues.map((issue, i) => ({ id: i, ...issue }))}
            columns={[
              {
                field: "severity",
                headerName: "Severity",
                width: 110,
                renderCell: (p) =>
                  p.value === "error" ? (
                    <Chip size="small" color="error" icon={<ErrorOutlineIcon />} label="Error" />
                  ) : (
                    <Chip size="small" color="warning" icon={<WarningAmberIcon />} label="Warning" />
                  ),
              },
              { field: "position", headerName: "Position", width: 140 },
              { field: "field", headerName: "Field", width: 150 },
              { field: "message", headerName: "Message", flex: 1 },
            ]}
          />
        </Stack>
      )}
    </Paper>
  );
}
