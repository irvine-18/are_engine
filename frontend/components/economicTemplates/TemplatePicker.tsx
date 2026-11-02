"use client";

import { useRouter } from "next/navigation";
import { Alert, Box, Button, Chip, MenuItem, Paper, Select, Stack, Typography, type SelectChangeEvent } from "@mui/material";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import FolderOpenOutlinedIcon from "@mui/icons-material/FolderOpenOutlined";
import AddIcon from "@mui/icons-material/Add";

import { useEconomicTemplates } from "@/stores/economicTemplates";
import { sectionsIncluded } from "@/lib/economicTemplates";

/** Select-only -- running a template's economic data happens on /economic/templates
 * (its "Run"/"Re-run" button), not here. Every page using this component just reads
 * back whatever that run produced. */
export function TemplatePicker() {
  const router = useRouter();
  const { templates, activeTemplate, setDefaultTemplate } = useEconomicTemplates();

  function handleChange(event: SelectChangeEvent) {
    const id = event.target.value;
    if (id) setDefaultTemplate(id, true);
  }

  return (
    <Paper
      sx={{
        p: 2,
        borderColor: activeTemplate ? "divider" : "warning.main",
      }}
    >
      <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between" alignItems={{ xs: "flex-start", md: "center" }}>
        <Stack direction="row" spacing={1.5} alignItems="flex-start" sx={{ minWidth: 0 }}>
          <Box
            sx={{
              display: "grid",
              placeItems: "center",
              width: 36,
              height: 36,
              borderRadius: 2,
              border: 1,
              borderColor: "divider",
              bgcolor: "background.default",
              color: activeTemplate ? "primary.main" : "warning.main",
              flexShrink: 0,
            }}
          >
            <DescriptionOutlinedIcon fontSize="small" />
          </Box>
          <Stack spacing={0.25} sx={{ minWidth: 0 }}>
            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" sx={{ rowGap: 0.5 }}>
              <Typography variant="subtitle1">Economic data template</Typography>
              {activeTemplate?.isDefault && <Chip size="small" color="info" variant="outlined" label="Default" />}
            </Stack>
            {activeTemplate ? (
              <Typography variant="body2" color="text.secondary" noWrap sx={{ maxWidth: { xs: "100%", md: 480 } }}>
                <Box component="strong" sx={{ color: "text.primary" }}>
                  {activeTemplate.name}
                </Box>
                {" · "}
                {sectionsIncluded(activeTemplate).join(", ") || "no sections included yet"}
              </Typography>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No template selected — select one or create a new one to continue.
              </Typography>
            )}
          </Stack>
        </Stack>

        <Stack direction="row" spacing={1} flexWrap="wrap" alignItems="center" sx={{ rowGap: 1, flexShrink: 0 }}>
          <Select
            size="small"
            displayEmpty
            value={activeTemplate?.id ?? ""}
            onChange={handleChange}
            disabled={templates.length === 0}
            sx={{ minWidth: 220 }}
          >
            {templates.length === 0 && (
              <MenuItem value="" disabled>
                No templates saved yet
              </MenuItem>
            )}
            {templates.map((t) => (
              <MenuItem key={t.id} value={t.id}>
                {t.name}
                {t.isDefault ? " (Default)" : ""}
              </MenuItem>
            ))}
          </Select>
          <Button
            size="small"
            variant="outlined"
            startIcon={<AddIcon fontSize="small" />}
            onClick={() => router.push("/economic/templates?action=new")}
          >
            Create
          </Button>
          <Button
            size="small"
            variant="outlined"
            startIcon={<FolderOpenOutlinedIcon fontSize="small" />}
            onClick={() => router.push("/economic/templates")}
          >
            Templates
          </Button>
        </Stack>
      </Stack>

      {activeTemplate?.lastRun?.inflationWarning && (
        <Alert severity="warning" sx={{ mt: 1.5 }}>
          {activeTemplate.lastRun.inflationWarning} Any inflation-linked position (e.g. an inflation-linked swap)
          will price with inflation treated as flat zero until this is fixed and the template is re-run.
        </Alert>
      )}
    </Paper>
  );
}
