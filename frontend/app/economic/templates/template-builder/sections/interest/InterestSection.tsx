"use client";

import { Accordion, AccordionDetails, AccordionSummary, Box, Button, FormControlLabel, Radio, RadioGroup, Stack, Typography } from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ShowChartIcon from "@mui/icons-material/ShowChart";
import EditIcon from "@mui/icons-material/Edit";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import dayjs from "dayjs";

import { SectionHeader } from "../../components/SectionHeader";
import { useAutoExpand } from "../../components/useAutoExpand";
import { INTEREST_SOURCE_MODE_LABELS, type InterestSectionConfig, type InterestSourceMode } from "@/lib/economicTemplates";

export function InterestSection({
  interest,
  onPatch,
  onOpenSwapRates,
}: {
  interest: InterestSectionConfig;
  onPatch: (patch: Partial<InterestSectionConfig>) => void;
  onOpenSwapRates: () => void;
}) {
  const [expanded, setExpanded] = useAutoExpand(interest.included);

  return (
    <Accordion expanded={expanded} onChange={(_, isExpanded) => setExpanded(isExpanded)}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <SectionHeader
          icon={<ShowChartIcon />}
          title="1. Interest"
          included={interest.included}
          onIncludedChange={(v) => onPatch({ included: v })}
        />
      </AccordionSummary>
      <AccordionDetails>
        {interest.included ? (
          <Stack spacing={2}>
            <RadioGroup
              value={interest.sourceMode}
              onChange={(e) => {
                const sourceMode = e.target.value as InterestSourceMode;
                onPatch({ sourceMode });
                if (sourceMode === "swap_rates") onOpenSwapRates();
              }}
            >
              {Object.entries(INTEREST_SOURCE_MODE_LABELS).map(([value, label]) => (
                <Box key={value}>
                  <FormControlLabel
                    value={value}
                    control={<Radio size="small" />}
                    label={label}
                    disabled={value === "upload_precomputed"}
                  />
                  {value === "eiopa_published" && interest.sourceMode === "eiopa_published" && (
                    <Box sx={{ pl: 4, pt: 1, pb: 1 }}>
                      <DatePicker
                        label="Publication month"
                        views={["year", "month"]}
                        openTo="month"
                        value={dayjs(`${interest.eiopaPublicationMonth}-01`)}
                        onChange={(value) => value && onPatch({ eiopaPublicationMonth: value.format("YYYY-MM") })}
                        slotProps={{ textField: { sx: { maxWidth: 260 } } }}
                      />
                    </Box>
                  )}
                </Box>
              ))}
            </RadioGroup>

            {interest.sourceMode === "swap_rates" && (
              <Box sx={{ pl: 4 }}>
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<EditIcon fontSize="small" />}
                    onClick={onOpenSwapRates}
                    sx={{ alignSelf: "flex-start" }}
                  >
                    {interest.liquidPoints.length > 0 ? "Edit swap rates, SW-parameters & SCR shocks" : "Enter swap rates, SW-parameters & SCR shocks"}
                  </Button>
                  {interest.liquidPoints.length > 0 && (
                    <Typography variant="caption" color="text.secondary">
                      {interest.liquidPoints.length} point{interest.liquidPoints.length === 1 ? "" : "s"} set
                    </Typography>
                  )}
                </Stack>
              </Box>
            )}
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary">
            Switch this section on to configure interest-rate input for this template.
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );
}
