import { useState } from "react";
import { Box, Button, Chip, Divider, IconButton, Menu, MenuItem, Paper, Stack, Typography } from "@mui/material";
import FolderIcon from "@mui/icons-material/Folder";
import MoreVertIcon from "@mui/icons-material/MoreVert";

import { fmtDate, fmtMoney } from "@/lib/format";
import type { PortfolioSummary } from "@/lib/sampleData/portfolio";

interface PortfolioListCardProps {
  portfolio: PortfolioSummary;
  onOpen: () => void;
  onRename: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
}

export function PortfolioListCard({ portfolio, onOpen, onRename, onDuplicate, onDelete }: PortfolioListCardProps) {
  const [menuAnchor, setMenuAnchor] = useState<HTMLElement | null>(null);

  return (
    <Paper sx={{ p: 2.5 }}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} justifyContent="space-between" alignItems={{ sm: "center" }}>
        <Stack direction="row" spacing={1.5} alignItems="center" sx={{ minWidth: 0 }}>
          <Box
            sx={{
              display: "grid",
              placeItems: "center",
              width: 40,
              height: 40,
              borderRadius: 2,
              border: 1,
              borderColor: "divider",
              bgcolor: "background.default",
              color: "primary.main",
              flexShrink: 0,
            }}
          >
            <FolderIcon fontSize="small" />
          </Box>
          <Stack spacing={0.5} sx={{ minWidth: 0 }}>
            <Typography variant="subtitle1" noWrap>
              {portfolio.name}
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ rowGap: 0.5 }}>
              <Chip size="small" variant="outlined" label={`${portfolio.positionCount} positions`} />
              <Chip size="small" variant="outlined" label={`Total MV ${fmtMoney(portfolio.totalMarketValue, portfolio.currency, true)}`} />
              <Chip
                size="small"
                variant="outlined"
                color={portfolio.lastRunAt ? "default" : "warning"}
                label={portfolio.lastRunAt ? `Last run ${fmtDate(portfolio.lastRunAt)}` : "Never run"}
              />
            </Stack>
          </Stack>
        </Stack>

        <Stack direction="row" spacing={1} alignItems="center" sx={{ flexShrink: 0 }}>
          <Button size="small" variant="contained" onClick={onOpen}>
            Open
          </Button>
          <IconButton size="small" onClick={(e) => setMenuAnchor(e.currentTarget)} aria-label={`${portfolio.name} actions`}>
            <MoreVertIcon fontSize="small" />
          </IconButton>
          <Menu anchorEl={menuAnchor} open={Boolean(menuAnchor)} onClose={() => setMenuAnchor(null)}>
            <MenuItem
              onClick={() => {
                onRename();
                setMenuAnchor(null);
              }}
            >
              Rename…
            </MenuItem>
            <MenuItem
              onClick={() => {
                onDuplicate();
                setMenuAnchor(null);
              }}
            >
              Duplicate
            </MenuItem>
            <Divider />
            <MenuItem
              sx={{ color: "error.main" }}
              onClick={() => {
                onDelete();
                setMenuAnchor(null);
              }}
            >
              Delete
            </MenuItem>
          </Menu>
        </Stack>
      </Stack>
    </Paper>
  );
}
