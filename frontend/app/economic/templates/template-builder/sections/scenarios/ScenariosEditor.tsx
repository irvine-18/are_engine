"use client";

import { useState } from "react";
import { Button, Chip, IconButton, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, Tooltip, Typography, Switch } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";

import { ScenarioFormDialog } from "./ScenarioFormDialog";
import {
  QUICK_ADD_PRESETS,
  formatApplyTo,
  formatEquityShift,
  formatInflationShift,
  formatInterestShift,
  type ScenarioDefinition,
} from "@/lib/scenarios";

export function ScenariosEditor({
  scenarios,
  onChange,
  interestUsesEiopaPublished,
}: {
  scenarios: ScenarioDefinition[];
  onChange: (scenarios: ScenarioDefinition[]) => void;
  interestUsesEiopaPublished: boolean;
}) {
  const [dialogOpen, setDialogOpen] = useState(false);

  function handleQuickAdd(preset: (typeof QUICK_ADD_PRESETS)[number]) {
    if (scenarios.some((s) => !s.builtIn && s.name === preset.label)) return;
    const scenario: ScenarioDefinition = {
      id: `user-${typeof crypto !== "undefined" ? crypto.randomUUID() : Date.now()}`,
      name: preset.label,
      category: preset.category,
      description: preset.description,
      active: true,
      builtIn: false,
      interestShock: preset.interestShock,
      interestApplyTo: "liquid_then_re_extrapolate",
      inflationShock: preset.inflationShock,
      inflationApplyTo: "liquid_then_re_extrapolate",
    };
    onChange([...scenarios, scenario]);
  }

  function handleCreate(scenario: ScenarioDefinition) {
    onChange([...scenarios, scenario]);
    setDialogOpen(false);
  }

  function handleToggleActive(id: string, active: boolean) {
    onChange(scenarios.map((s) => (s.id === id ? { ...s, active } : s)));
  }

  function handleRemove(id: string) {
    onChange(scenarios.filter((s) => s.id !== id));
  }

  return (
    <Stack spacing={2}>
      <Typography variant="body2" color="text.secondary">
        Scenarios are specified per template and feed the Interest, Inflation and HICP sections below.
      </Typography>

      <Stack spacing={1}>
        <Typography variant="caption" color="text.secondary">
          Quick-add presets
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ rowGap: 1 }}>
          {QUICK_ADD_PRESETS.map((preset) => (
            <Button key={preset.key} size="small" variant="outlined" startIcon={<AddIcon fontSize="small" />} onClick={() => handleQuickAdd(preset)}>
              {preset.label}
            </Button>
          ))}
          <Button size="small" variant="contained" startIcon={<AddIcon fontSize="small" />} onClick={() => setDialogOpen(true)}>
            New scenario
          </Button>
        </Stack>
      </Stack>

      <Paper variant="outlined" sx={{ overflowX: "auto" }}>
        <Table size="small" sx={{ minWidth: 900 }}>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Interest shift</TableCell>
              <TableCell>Inflation shift</TableCell>
              <TableCell>Equity shift</TableCell>
              <TableCell align="center">Active</TableCell>
              <TableCell align="center">Built-in</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {scenarios.map((scenario) => (
              <TableRow key={scenario.id} hover>
                <TableCell sx={{ fontWeight: 600 }}>{scenario.name}</TableCell>
                <TableCell>
                  <Chip size="small" variant={scenario.builtIn ? "filled" : "outlined"} label={scenario.category} />
                </TableCell>
                <TableCell>
                  <Stack spacing={0}>
                    <span>{formatInterestShift(scenario)}</span>
                    {scenario.interestShock.type !== "none" && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {formatApplyTo(scenario.interestApplyTo)}
                      </Typography>
                    )}
                  </Stack>
                </TableCell>
                <TableCell>
                  <Stack spacing={0}>
                    <span>{formatInflationShift(scenario)}</span>
                    {scenario.inflationShock.type !== "none" && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {formatApplyTo(scenario.inflationApplyTo)}
                      </Typography>
                    )}
                  </Stack>
                </TableCell>
                <TableCell>{formatEquityShift(scenario)}</TableCell>
                <TableCell align="center">
                  <Switch size="small" checked={scenario.active} onChange={(e) => handleToggleActive(scenario.id, e.target.checked)} />
                </TableCell>
                <TableCell align="center">
                  {scenario.builtIn ? (
                    <Tooltip title="Built-in scenarios cannot be deleted">
                      <LockOutlinedIcon fontSize="small" sx={{ color: "text.secondary" }} />
                    </Tooltip>
                  ) : (
                    "—"
                  )}
                </TableCell>
                <TableCell align="right">
                  {!scenario.builtIn && (
                    <IconButton size="small" onClick={() => handleRemove(scenario.id)} aria-label={`remove ${scenario.name}`}>
                      <DeleteOutlineIcon fontSize="small" />
                    </IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <ScenarioFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onCreate={handleCreate}
        interestUsesEiopaPublished={interestUsesEiopaPublished}
      />
    </Stack>
  );
}
