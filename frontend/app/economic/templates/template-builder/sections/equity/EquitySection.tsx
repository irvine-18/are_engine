"use client";

import { Accordion, AccordionDetails, AccordionSummary, Box, Divider, FormControlLabel, Radio, RadioGroup, Stack, TextField, Typography } from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import dayjs from "dayjs";

import { SectionHeader } from "../../components/SectionHeader";
import { useAutoExpand } from "../../components/useAutoExpand";
import { getEiopaSymmetricAdjustment } from "../../utils/eiopaSymmetricAdjustment";
import { fmtRate } from "@/lib/format";
import type { EquitySectionConfig, SymmetricAdjustmentSourceMode } from "@/lib/economicTemplates";

const SYMMETRIC_ADJUSTMENT_SOURCE_MODE_LABELS: Record<SymmetricAdjustmentSourceMode, string> = {
  eiopa_published: "EIOPA published",
  manual: "Enter manually",
};

export function EquitySection({
  equity,
  onPatch,
}: {
  equity: EquitySectionConfig;
  onPatch: (patch: Partial<EquitySectionConfig>) => void;
}) {
  const [expanded, setExpanded] = useAutoExpand(equity.included);

  return (
    <Accordion expanded={expanded} onChange={(_, isExpanded) => setExpanded(isExpanded)}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <SectionHeader
          icon={<TrendingUpIcon />}
          title="3. Equity Adjustment"
          included={equity.included}
          onIncludedChange={(v) => onPatch({ included: v })}
        />
      </AccordionSummary>
      <AccordionDetails>
        {equity.included ? (
          <Stack spacing={2}>
            <Typography variant="subtitle2">EIOPA equity symmetric adjustment</Typography>

            <RadioGroup
              value={equity.symmetricAdjustmentSourceMode}
              onChange={(e) => {
                const sourceMode = e.target.value as SymmetricAdjustmentSourceMode;
                onPatch(
                  sourceMode === "eiopa_published"
                    ? { symmetricAdjustmentSourceMode: sourceMode, symmetricAdjustment: getEiopaSymmetricAdjustment(equity.eiopaPublicationMonth) }
                    : { symmetricAdjustmentSourceMode: sourceMode },
                );
              }}
            >
              {Object.entries(SYMMETRIC_ADJUSTMENT_SOURCE_MODE_LABELS).map(([value, label]) => (
                <FormControlLabel key={value} value={value} control={<Radio size="small" />} label={label} />
              ))}
            </RadioGroup>

            {equity.symmetricAdjustmentSourceMode === "eiopa_published" ? (
              <Box sx={{ pl: 4 }}>
                <Stack direction="row" spacing={2} alignItems="flex-start" flexWrap="wrap">
                  <DatePicker
                    label="Publication month"
                    views={["year", "month"]}
                    openTo="month"
                    value={dayjs(`${equity.eiopaPublicationMonth}-01`)}
                    onChange={(value) => {
                      if (!value) return;
                      const eiopaPublicationMonth = value.format("YYYY-MM");
                      onPatch({ eiopaPublicationMonth, symmetricAdjustment: getEiopaSymmetricAdjustment(eiopaPublicationMonth) });
                    }}
                    slotProps={{ textField: { sx: { maxWidth: 260 } } }}
                  />
                  <TextField
                    label="Published symmetric adjustment"
                    value={fmtRate(equity.symmetricAdjustment)}
                    slotProps={{ input: { readOnly: true } }}
                    sx={{ maxWidth: 260 }}
                  />
                </Stack>
              </Box>
            ) : (
              <Box sx={{ pl: 4 }}>
                <TextField
                  label="Symmetric adjustment (%)"
                  type="number"
                  value={equity.symmetricAdjustment * 100}
                  onChange={(e) => onPatch({ symmetricAdjustment: Number(e.target.value) / 100 })}
                  sx={{ maxWidth: 260 }}
                  helperText={fmtRate(equity.symmetricAdjustment)}
                />
              </Box>
            )}

            <Divider />

            <Stack direction="row" spacing={2} flexWrap="wrap">
              <TextField
                label="Type 1 base shock (%)"
                type="number"
                value={equity.type1BaseShock * 100}
                onChange={(e) => onPatch({ type1BaseShock: Number(e.target.value) / 100 })}
                sx={{ maxWidth: 240 }}
                helperText={fmtRate(equity.type1BaseShock)}
              />
              <TextField
                label="Type 2 base shock (%)"
                type="number"
                value={equity.type2BaseShock * 100}
                onChange={(e) => onPatch({ type2BaseShock: Number(e.target.value) / 100 })}
                sx={{ maxWidth: 240 }}
                helperText={fmtRate(equity.type2BaseShock)}
              />
            </Stack>
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary">
            Switch this section on to set the equity symmetric adjustment.
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );
}
