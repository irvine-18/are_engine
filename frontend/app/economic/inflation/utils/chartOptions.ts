import type { ChartOptions } from "chart.js";
import type { chartPalette } from "@/theme/theme";

type ChartPalette = (typeof chartPalette)["light"];

/** Shared Chart.js line-chart options for the Inflation page's two charts --
 * matches the styling/legend-click-to-toggle behaviour of /economic/curves's
 * `CurveRateChart.tsx`. Canvas rendering can't resolve this app's CSS-variable
 * theme, so callers pass the literal palette for the active colour scheme
 * (`theme/theme.ts`'s `chartPalette`). */
export function buildLineChartOptions(palette: ChartPalette, xLabel: string, yLabel: string): ChartOptions<"line"> {
  return {
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
        title: { display: true, text: xLabel, color: palette.textSecondary },
        ticks: {
          color: palette.textSecondary,
          maxRotation: 0,
          minRotation: 0,
          autoSkip: false,
          // One label every 5 points, horizontal -- a label per point both
          // crowds the axis and forces Chart.js to rotate them to fit.
          callback(value, index) {
            return index % 5 === 0 ? this.getLabelForValue(Number(value)) : undefined;
          },
        },
        grid: { display: false },
      },
      y: {
        title: { display: true, text: yLabel, color: palette.textSecondary },
        ticks: { color: palette.textSecondary },
        grid: { display: false },
      },
    },
  };
}
