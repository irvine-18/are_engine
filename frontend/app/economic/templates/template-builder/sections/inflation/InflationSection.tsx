"use client";

import { Accordion, AccordionDetails, AccordionSummary, Box, Button, Divider, FormControlLabel, Radio, RadioGroup, Stack, TextField, Typography } from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import TimelineIcon from "@mui/icons-material/Timeline";
import InsightsIcon from "@mui/icons-material/Insights";
import EditIcon from "@mui/icons-material/Edit";

import { SectionHeader } from "../../components/SectionHeader";
import { useAutoExpand } from "../../components/useAutoExpand";
import { INFLATION_SOURCE_MODE_LABELS, type HicpSectionConfig, type InflationSectionConfig, type InflationSourceMode } from "@/lib/economicTemplates";

export function InflationSection({
  inflation,
  onPatchInflation,
  onOpenSwapRates,
  hicp,
  onPatchHicp,
}: {
  inflation: InflationSectionConfig;
  onPatchInflation: (patch: Partial<InflationSectionConfig>) => void;
  onOpenSwapRates: () => void;
  hicp: HicpSectionConfig;
  onPatchHicp: (patch: Partial<HicpSectionConfig>) => void;
}) {
  const [expanded, setExpanded] = useAutoExpand(inflation.included);

  return (
    <Accordion expanded={expanded} onChange={(_, isExpanded) => setExpanded(isExpanded)}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <SectionHeader
          icon={<TimelineIcon />}
          title="2. Inflation"
          included={inflation.included}
          onIncludedChange={(v) => onPatchInflation({ included: v })}
        />
      </AccordionSummary>
      <AccordionDetails>
        {inflation.included ? (
          <Stack spacing={2}>
            <RadioGroup
              value={inflation.sourceMode}
              onChange={(e) => {
                const sourceMode = e.target.value as InflationSourceMode;
                onPatchInflation({ sourceMode });
                if (sourceMode === "swap_rates") onOpenSwapRates();
              }}
            >
              {Object.entries(INFLATION_SOURCE_MODE_LABELS).map(([value, label]) => (
                <FormControlLabel
                  key={value}
                  value={value}
                  control={<Radio size="small" />}
                  label={label}
                  disabled={value === "upload_precomputed"}
                />
              ))}
            </RadioGroup>

            {inflation.sourceMode === "swap_rates" && (
              <Box sx={{ pl: 4 }}>
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<EditIcon fontSize="small" />}
                    onClick={onOpenSwapRates}
                    sx={{ alignSelf: "flex-start" }}
                  >
                    {inflation.liquidPoints.length > 0 ? "Edit swap rates & SW-parameters" : "Enter swap rates & SW-parameters"}
                  </Button>
                  {inflation.liquidPoints.length > 0 && (
                    <Typography variant="caption" color="text.secondary">
                      {inflation.liquidPoints.length} point{inflation.liquidPoints.length === 1 ? "" : "s"} set
                    </Typography>
                  )}
                </Stack>
              </Box>
            )}

            <Divider />

            <SectionHeader icon={<InsightsIcon />} title="HICP" included={hicp.included} onIncludedChange={(v) => onPatchHicp({ included: v })} />

            {hicp.included ? (
              <Stack direction="row" spacing={2} flexWrap="wrap">
                <TextField
                  label="Latest observation date"
                  type="date"
                  value={hicp.latestObservationDate}
                  onChange={(e) => onPatchHicp({ latestObservationDate: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
                <TextField
                  label="Latest observation value"
                  type="number"
                  value={hicp.latestObservationValue}
                  onChange={(e) => onPatchHicp({ latestObservationValue: Number(e.target.value) })}
                />
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Switch this on to set the latest HICP observation.
              </Typography>
            )}
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary">
            Switch this section on to configure inflation input for this template.
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );
}
