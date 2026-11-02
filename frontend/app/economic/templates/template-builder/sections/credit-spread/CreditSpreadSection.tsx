"use client";

import { Accordion, AccordionDetails, AccordionSummary, Button, FormControlLabel, Link, Radio, RadioGroup, Stack, Typography } from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PriceChangeIcon from "@mui/icons-material/PriceChange";

import { SectionHeader } from "../../components/SectionHeader";
import { useAutoExpand } from "../../components/useAutoExpand";
import { CreditSpreadEditor } from "./CreditSpreadEditor";
import { solvencyIiCreditSpreadGuideline, type CreditSpreadSectionConfig, type CreditSpreadSourceMode } from "@/lib/economicTemplates";

const SOLVENCY_II_SPREAD_RISK_URL = "https://www.eiopa.europa.eu/rulebook/solvency-ii-single-rulebook/article-5796_en";

const CREDIT_SPREAD_SOURCE_MODE_LABELS: Record<CreditSpreadSourceMode, string> = {
  solvency_ii_guideline: "Use Solvency II guideline",
  manual: "Enter manually",
};

export function CreditSpreadSection({
  creditSpread,
  onPatch,
}: {
  creditSpread: CreditSpreadSectionConfig;
  onPatch: (patch: Partial<CreditSpreadSectionConfig>) => void;
}) {
  const [expanded, setExpanded] = useAutoExpand(creditSpread.included);
  const isGuideline = creditSpread.sourceMode === "solvency_ii_guideline";

  return (
    <Accordion expanded={expanded} onChange={(_, isExpanded) => setExpanded(isExpanded)}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <SectionHeader
          icon={<PriceChangeIcon />}
          title="4. Credit Spread"
          included={creditSpread.included}
          onIncludedChange={(v) => onPatch({ included: v })}
        />
      </AccordionSummary>
      <AccordionDetails>
        {creditSpread.included ? (
          <Stack spacing={2}>
            <RadioGroup
              value={creditSpread.sourceMode}
              onChange={(e) => {
                const sourceMode = e.target.value as CreditSpreadSourceMode;
                onPatch(
                  sourceMode === "solvency_ii_guideline"
                    ? { sourceMode, ...solvencyIiCreditSpreadGuideline() }
                    : { sourceMode },
                );
              }}
            >
              {Object.entries(CREDIT_SPREAD_SOURCE_MODE_LABELS).map(([value, label]) => (
                <FormControlLabel key={value} value={value} control={<Radio size="small" />} label={label} />
              ))}
            </RadioGroup>

            {!isGuideline && (
              <Button
                size="small"
                onClick={() => onPatch({ cqsMapping: [], spreadCoefficients: [] })}
                sx={{ alignSelf: "flex-start" }}
              >
                Clear
              </Button>
            )}

            <CreditSpreadEditor
              cqsMapping={creditSpread.cqsMapping}
              spreadCoefficients={creditSpread.spreadCoefficients}
              onChangeCqsMapping={(cqsMapping) => onPatch({ cqsMapping })}
              onChangeSpreadCoefficients={(spreadCoefficients) => onPatch({ spreadCoefficients })}
              locked={isGuideline}
            />

            {isGuideline && (
              <Typography variant="caption" color="text.secondary">
                Standard formula values per{" "}
                <Link href={SOLVENCY_II_SPREAD_RISK_URL} target="_blank" rel="noopener noreferrer">
                  Solvency II Delegated Regulation (EU) 2015/35, Article 176 (spread risk on bonds and loans)
                </Link>
                .
              </Typography>
            )}
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary">
            Switch this section on to configure the CQS mapping and spread risk coefficients used by
            spread-risk-bearing positions (e.g. corporate bonds) under this template.
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );
}
