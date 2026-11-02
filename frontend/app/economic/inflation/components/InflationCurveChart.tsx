"use client";

import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from "chart.js";
import { Line } from "react-chartjs-2";
import { useColorScheme } from "@mui/material/styles";
import { Box } from "@mui/material";

import { ChartCard } from "@/components/charts/ChartCard";
import { chartPalette } from "@/theme/theme";
import { scenarioColor } from "@/lib/scenarioColor";
import { buildLineChartOptions } from "../utils/chartOptions";
import type { InflationPoint } from "@/lib/sampleData/inflation";
import type { NamedSeries } from "../utils/inflationScenarios";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

interface InflationCurveChartProps {
  costInfl: InflationPoint[];
  scenarioSeries: NamedSeries[];
}

export function InflationCurveChart({ costInfl, scenarioSeries }: InflationCurveChartProps) {
  const { mode, systemMode } = useColorScheme();
  const resolvedMode = (mode === "system" ? systemMode : mode) ?? "light";
  const palette = chartPalette[resolvedMode];

  const data = {
    labels: costInfl.map((p) => p.year),
    datasets: [
      {
        label: "Base",
        data: costInfl.map((p) => p.rate * 100),
        borderColor: scenarioColor(resolvedMode, 0),
        backgroundColor: scenarioColor(resolvedMode, 0),
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2,
        cubicInterpolationMode: "monotone" as const,
      },
      ...scenarioSeries.map((s) => ({
        label: s.name,
        data: s.points.map((p) => p.rate * 100),
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
      title="Cost-inflation curve"
      chart={
        <Box sx={{ height: 340 }}>
          <Line data={data} options={buildLineChartOptions(palette, "Year", "Rate (%)")} />
        </Box>
      }
    />
  );
}
