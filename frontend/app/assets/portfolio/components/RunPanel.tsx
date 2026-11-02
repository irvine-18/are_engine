import { Button, Paper, Stack } from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";

interface RunPanelProps {
  onRun: () => void;
  disabled: boolean;
}

export function RunPanel({ onRun, disabled }: RunPanelProps) {
  return (
    <Paper
      elevation={0}
      sx={{
        position: "sticky",
        bottom: 0,
        p: 2,
        borderRadius: 3,
        boxShadow: "0 -4px 16px rgba(16,17,30,0.08)",
        zIndex: 1,
      }}
    >
      <Stack direction={{ xs: "column", lg: "row" }} spacing={2} alignItems={{ lg: "center" }} justifyContent="flex-end">
        <Button
          variant="contained"
          startIcon={<PlayArrowIcon />}
          onClick={onRun}
          disabled={disabled}
          sx={{ flexShrink: 0 }}
        >
          Run portfolio SCR
        </Button>
      </Stack>
    </Paper>
  );
}
