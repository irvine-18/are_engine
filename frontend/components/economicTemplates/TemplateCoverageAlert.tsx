"use client";

import { useRouter } from "next/navigation";
import { Alert, AlertTitle, Box, Button, Typography } from "@mui/material";

import type { CoverageIssue } from "@/lib/templateValidation";

export function TemplateCoverageAlert({ issues }: { issues: CoverageIssue[] }) {
  const router = useRouter();

  if (issues.length === 0) return null;

  return (
    <Alert
      severity="warning"
      action={
        <Button size="small" onClick={() => router.push("/economic/templates")}>
          Review template
        </Button>
      }
    >
      <AlertTitle>Active template may not cover everything this run needs</AlertTitle>
      <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
        {issues.map((issue) => (
          <Typography key={issue.key} component="li" variant="body2">
            {issue.message}
          </Typography>
        ))}
      </Box>
    </Alert>
  );
}
