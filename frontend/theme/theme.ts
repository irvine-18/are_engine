"use client";

import { createTheme } from "@mui/material/styles";

declare module "@mui/material/styles" {
  interface TypographyVariants {
    number: React.CSSProperties;
  }
  interface TypographyVariantsOptions {
    number?: React.CSSProperties;
  }
}

declare module "@mui/material/Typography" {
  interface TypographyPropsVariantOverrides {
    number: true;
  }
}

/** Colour tokens for the always-dark app sidebar. Kept outside the MUI colour
 * scheme because the reference design (frontend/solvency-ii-asset-risk-app)
 * keeps the sidebar dark in both light and dark mode -- only the content area
 * switches. */
export const sidebarTokens = {
  background: "#1b1e2b",
  backgroundDark: "#121420",
  foreground: "#e7e8f3",
  foregroundMuted: "rgba(231, 232, 243, 0.65)",
  accent: "#2a2e42",
  accentForeground: "#f7f7fb",
  border: "rgba(255, 255, 255, 0.08)",
  primary: "#9c8cf0",
};

/** Diverging semantic colours for scenario-overlay charts, shared by /economic/curves
 * and /economic/inflation: blue for a positive shift, red for a negative one,
 * intensity scaling with the shift's magnitude (see `lib/scenarioColor.ts`).
 * `negative` reuses the theme's own `error` colour per mode (already this app's
 * "negatives are red" convention); `neutral` reuses `secondary`. `positive` has no
 * existing theme slot, so it's defined here rather than hardcoded in a chart
 * component. */
export const curveScenarioColors = {
  light: { positive: "#2a78d6", negative: "#d6453e", neutral: "#64748a" },
  dark: { positive: "#3987e5", negative: "#e8736c", neutral: "#9aa3b8" },
};

/** Literal per-mode text/grid/surface colours for canvas-rendered charts (Chart.js),
 * which can't resolve the CSS custom properties `theme.palette.*` otherwise returns
 * in this app's `cssVariables` theme. Mirrors the same light/dark values passed into
 * `colorSchemes` below -- kept as plain literals here for that reason, not duplicated
 * by oversight. */
export const chartPalette = {
  light: { textPrimary: "#1d2030", textSecondary: "#686f82", divider: "#e6e7ee", paper: "#ffffff" },
  dark: { textPrimary: "#eef0f7", textSecondary: "#a4a9bd", divider: "rgba(255, 255, 255, 0.1)", paper: "#1a1c29" },
};

export const theme = createTheme({
  cssVariables: { colorSchemeSelector: "data" },
  colorSchemes: {
    light: {
      palette: {
        primary: { main: "#5847d6", contrastText: "#ffffff" },
        secondary: { main: "#64748a" },
        error: { main: "#d6453e" },
        warning: { main: "#b4790f", light: "#fdf1cf", dark: "#8a5a08" },
        success: { main: "#1f8a5f" },
        background: { default: "#f8f8fb", paper: "#ffffff" },
        text: { primary: "#1d2030", secondary: "#686f82" },
        divider: "#e6e7ee",
      },
    },
    dark: {
      palette: {
        primary: { main: "#a596f5", contrastText: "#1a1b2b" },
        secondary: { main: "#9aa3b8" },
        error: { main: "#e8736c" },
        warning: { main: "#e4b454", light: "#3a2f14", dark: "#f0c570" },
        success: { main: "#4fcf98" },
        background: { default: "#14151f", paper: "#1a1c29" },
        text: { primary: "#eef0f7", secondary: "#a4a9bd" },
        divider: "rgba(255, 255, 255, 0.1)",
      },
    },
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily:
      '"Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif',
    fontSize: 14,
    h1: { fontWeight: 700, fontSize: "2.75rem", letterSpacing: -0.3, lineHeight: 1.15 },
    h2: { fontWeight: 700, fontSize: "2.25rem", letterSpacing: -0.25, lineHeight: 1.2 },
    h3: { fontWeight: 700, fontSize: "1.75rem", letterSpacing: -0.2, lineHeight: 1.25 },
    h4: { fontWeight: 700, fontSize: "1.5rem", letterSpacing: -0.15, lineHeight: 1.3 },
    h5: {
      fontWeight: 700,
      fontSize: "1.4rem",
      letterSpacing: -0.15,
      lineHeight: 1.3,
    },
    h6: { fontWeight: 700, fontSize: "1.0625rem", letterSpacing: -0.1, lineHeight: 1.35 },
    subtitle1: { fontWeight: 650, fontSize: "0.9375rem", lineHeight: 1.5 },
    subtitle2: { fontWeight: 700, fontSize: "0.875rem", lineHeight: 1.5, letterSpacing: -0.05 },
    body1: { fontSize: "0.9375rem", lineHeight: 1.65 },
    body2: { fontSize: "0.875rem", lineHeight: 1.65 },
    caption: { fontSize: "0.75rem", lineHeight: 1.5 },
    button: { fontWeight: 650, letterSpacing: 0.1 },
    overline: {
      fontSize: "0.68rem",
      fontWeight: 700,
      letterSpacing: "0.1em",
      lineHeight: 1.6,
    },
    number: {
      fontVariantNumeric: "tabular-nums",
      fontFamily: "'Roboto Mono', monospace",
    },
  },
  components: {
    MuiTextField: { defaultProps: { size: "small" } },
    MuiSelect: { defaultProps: { size: "small" } },
    MuiInputLabel: {
      styleOverrides: {
        root: { fontSize: "0.875rem", fontWeight: 500 },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: { borderRadius: 10 },
        input: { fontSize: "0.9rem" },
      },
    },
    MuiFormHelperText: {
      styleOverrides: {
        root: { fontSize: "0.72rem", marginLeft: 2, marginRight: 2 },
      },
    },
    MuiButton: {
      defaultProps: { size: "small" },
      styleOverrides: {
        root: { textTransform: "none", fontWeight: 650, borderRadius: 8, letterSpacing: 0.1 },
      },
    },
    MuiTableCell: {
      defaultProps: { size: "small" },
      styleOverrides: {
        head: { fontWeight: 700, fontSize: "0.75rem", letterSpacing: 0.2 },
      },
    },
    MuiPaper: {
      defaultProps: { variant: "outlined" },
      styleOverrides: {
        root: { backgroundImage: "none" },
      },
    },
    MuiCard: {
      defaultProps: { variant: "outlined" },
      styleOverrides: {
        root: { backgroundImage: "none" },
      },
    },
    MuiCardHeader: {
      styleOverrides: {
        title: { fontWeight: 700, fontSize: "1rem" },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: { fontWeight: 700, fontSize: "1.15rem" },
      },
    },
    MuiChip: {
      defaultProps: { size: "small" },
      styleOverrides: { root: { fontWeight: 650 } },
    },
    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: 10, fontSize: "0.825rem" },
        message: { lineHeight: 1.55 },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: { minHeight: 36 },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: { minHeight: 36, textTransform: "none", fontWeight: 650 },
      },
    },
    MuiStepper: {
      styleOverrides: {
        root: { background: "transparent" },
      },
    },
    MuiStepLabel: {
      styleOverrides: {
        label: {
          fontWeight: 600,
          fontSize: "0.95rem",
          "&.Mui-active": { fontWeight: 700 },
          "&.Mui-completed": { fontWeight: 650 },
        },
        iconContainer: { paddingRight: 14 },
      },
    },
    MuiStepIcon: {
      styleOverrides: {
        root: ({ theme }) => ({
          fontSize: 30,
          color: theme.vars.palette.action.disabledBackground,
          "&.Mui-active": { color: theme.vars.palette.primary.main },
          "&.Mui-completed": { color: theme.vars.palette.success.main },
        }),
        text: { fontSize: "0.75rem", fontWeight: 700 },
      },
    },
    MuiStepContent: {
      styleOverrides: {
        root: { borderLeftWidth: 2, marginLeft: 14, paddingLeft: 28, paddingBottom: 28 },
      },
    },
    MuiStepConnector: {
      styleOverrides: {
        line: { borderLeftWidth: 2 },
      },
    },
  },
});
