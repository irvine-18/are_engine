"use client";

import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from "chart.js";
import { Line } from "react-chartjs-2";
import { useColorScheme } from "@mui/material/styles";
import { Box } from "@mui/material";

import { ChartCard } from "@/components/charts/ChartCard";
import { chartPalette } from "@/theme/theme";
import { scenarioColor } from "@/lib/scenarioColor";
import { buildLineChartOptions } from "../utils/chartOptions";
import type { HicpPoint } from "@/lib/sampleData/inflation";
import type { NamedHicpSeries } from "../utils/inflationScenarios";
import type { InflationIndexName } from "./InflationIndexBanner";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

interface HicpProjectionChartProps {
  indexName: InflationIndexName;
  observed: HicpPoint[];
  hicpProjections: NamedHicpSeries[];
}

export function HicpProjectionChart({ indexName, observed, hicpProjections }: HicpProjectionChartProps) {
  const { mode, systemMode } = useColorScheme();
  const resolvedMode = (mode === "system" ? systemMode : mode) ?? "light";
  const palette = chartPalette[resolvedMode];

  const data = {
    labels: [...observed.map((p) => p.period), ...(hicpProjections[0]?.points.map((p) => p.period) ?? [])],
    datasets: [
      {
        label: "Observed",
        data: observed.map((p) => p.index),
        borderColor: scenarioColor(resolvedMode, 0),
        backgroundColor: scenarioColor(resolvedMode, 0),
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2,
        cubicInterpolationMode: "monotone" as const,
      },
      ...hicpProjections.map((s) => ({
        label: s.name,
        data: [...Array(observed.length - 1).fill(null), observed[observed.length - 1].index, ...s.points.map((p) => p.index)],
        borderColor: scenarioColor(resolvedMode, s.shiftBp),
        backgroundColor: scenarioColor(resolvedMode, s.shiftBp),
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2,
        cubicInterpolationMode: "monotone" as const,
      })),
    ],
  };

  return (
    <ChartCard
      title={`${indexName} history and projection`}
      chart={
        <Box sx={{ height: 300 }}>
          <Line data={data} options={buildLineChartOptions(palette, "Period", "Index")} />
        </Box>
      }
    />
  );
}
