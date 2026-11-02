"use client";

import { useMemo } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  type ChartOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { useColorScheme } from "@mui/material/styles";
import { Box } from "@mui/material";

import { ChartCard } from "@/components/charts/ChartCard";
import { buildCurveLineSeries, curveChartYears } from "../utils/curveChartSeries";
import { chartPalette } from "@/theme/theme";
import type { ScenarioDefinition } from "@/lib/scenarios";
import type { CurveSet, ScenarioCurve } from "@/lib/api/types";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

interface CurveRateChartProps {
  curveSet: CurveSet;
  baseScenario: ScenarioCurve | undefined;
  upScenario: ScenarioCurve | undefined;
  downScenario: ScenarioCurve | undefined;
  customScenarios: ScenarioDefinition[];
}

export function CurveRateChart({ curveSet, baseScenario, upScenario, downScenario, customScenarios }: CurveRateChartProps) {
  const { mode, systemMode } = useColorScheme();
  const resolvedMode = (mode === "system" ? systemMode : mode) ?? "light";
  const palette = chartPalette[resolvedMode];

  const series = useMemo(
    () => buildCurveLineSeries(resolvedMode, baseScenario, upScenario, downScenario, customScenarios),
    [resolvedMode, baseScenario, upScenario, downScenario, customScenarios],
  );

  if (!baseScenario) return null;

  const data = {
    labels: curveChartYears(baseScenario),
    datasets: series.map((s) => ({
      id: s.id,
      label: s.label,
      data: s.data,
      borderColor: s.color,
      backgroundColor: s.color,
      pointRadius: 0,
      pointHoverRadius: 4,
      borderWidth: 2,
      // cubicInterpolationMode: "monotone" as const,
      tension: 0.02,
    })),
  };

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: {
        position: "top",
        labels: { color: palette.textSecondary },
        // Clicking a legend entry toggles that dataset's visibility by default --
        // no custom handler needed.
      },
      tooltip: {
        backgroundColor: palette.paper,
        titleColor: palette.textPrimary,
        bodyColor: palette.textSecondary,
        borderColor: palette.divider,
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        title: { display: true, text: "Year", color: palette.textSecondary },
        ticks: {
          color: palette.textSecondary,
          maxRotation: 0,
          minRotation: 0,
          autoSkip: false,
          // One label every 5 points, horizontal -- a label per year both
          // crowds the axis and forces Chart.js to rotate them to fit.
          callback(value, index) {
            return index % 5 === 0 ? this.getLabelForValue(Number(value)) : undefined;
          },
        },
        grid: { display: false },
      },
      y: {
        title: { display: true, text: "Spot rate (%)", color: palette.textSecondary },
        ticks: { color: palette.textSecondary },
        grid: { display: false },
      },
    },
  };

  return (
    <ChartCard
      title={`${curveSet} — spot rate by tenor`}
      chart={
        <Box sx={{ height: 560 }}>
          <Line data={data} options={options} />
        </Box>
      }
    />
  );
}
