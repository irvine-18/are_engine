"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Avatar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import ShieldOutlinedIcon from "@mui/icons-material/ShieldOutlined";
import ApartmentOutlinedIcon from "@mui/icons-material/ApartmentOutlined";
import ShowChartIcon from "@mui/icons-material/ShowChart";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import FolderIcon from "@mui/icons-material/Folder";
import AssessmentIcon from "@mui/icons-material/Assessment";

import { sidebarTokens } from "@/theme/theme";
import { HeaderActions } from "@/components/layout/HeaderActions";

const DRAWER_WIDTH = 272;

const NAV_GROUPS = [
  {
    label: "Economic Engine",
    items: [
      // "/economic/inflation" is the Inflation tab of the same EconomicDataPage as
      // "/economic/curves" (no separate nav entry) -- matched too so this item stays
      // highlighted while on that tab.
      {
        href: "/economic/curves",
        matches: ["/economic/curves", "/economic/inflation"],
        label: "Curves",
        icon: <ShowChartIcon fontSize="small" />,
      },
      {
        href: "/economic/templates",
        label: "Templates",
        icon: <DescriptionOutlinedIcon fontSize="small" />,
      },
    ],
  },
  {
    label: "Asset Market Risk",
    items: [
      {
        href: "/assets/single",
        label: "Single Asset",
        icon: <AccountBalanceIcon fontSize="small" />,
      },
      {
        href: "/assets/portfolio",
        label: "Portfolio Construction",
        icon: <FolderIcon fontSize="small" />,
      },
      {
        href: "/assets/runs",
        matches: ["/assets/runs", "/assets/results"],
        label: "SCR Results",
        icon: <AssessmentIcon fontSize="small" />,
      },
    ],
  },
];

function BrandMark() {
  return (
    <Stack
      component={Link}
      href="/economic/curves"
      direction="row"
      spacing={1.5}
      alignItems="center"
      sx={{ textDecoration: "none" }}
    >
      <Box
        sx={{
          display: "grid",
          placeItems: "center",
          width: 40,
          height: 40,
          borderRadius: 2.5,
          bgcolor: sidebarTokens.primary,
          color: sidebarTokens.backgroundDark,
          flexShrink: 0,
          boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
        }}
      >
        <ShieldOutlinedIcon fontSize="small" />
      </Box>
      <Box sx={{ minWidth: 0 }}>
        <Typography
          variant="body2"
          fontWeight={700}
          sx={{ color: sidebarTokens.foreground }}
          noWrap
        >
          Asset Market Risk Engine
        </Typography>
        <Typography
          variant="overline"
          sx={{
            color: sidebarTokens.foregroundMuted,
            fontSize: "0.58rem",
            lineHeight: 1.4,
          }}
        >
          Actuarial workbench
        </Typography>
      </Box>
    </Stack>
  );
}

function SidebarContent({
  pathname,
  onNavigate,
}: {
  pathname: string;
  onNavigate?: () => void;
}) {
  return (
    <Stack sx={{ height: "100%", color: sidebarTokens.foreground }}>
      <Box sx={{ px: 2.5, pt: 2.5, pb: 2 }}>
        <BrandMark />
      </Box>

      <Box sx={{ flex: 1, overflowY: "auto", px: 1.5, pb: 2 }}>
        <Typography
          variant="overline"
          sx={{
            display: "block",
            color: sidebarTokens.foregroundMuted,
            fontSize: "0.58rem",
            px: 1.5,
            mb: 1.5,
          }}
        >
          Workspace
        </Typography>
        <Stack spacing={3}>
          {NAV_GROUPS.map((group) => (
            <Box key={group.label}>
              <Typography
                variant="overline"
                sx={{
                  display: "block",
                  color: sidebarTokens.foregroundMuted,
                  fontSize: "0.58rem",
                  px: 1.5,
                  mb: 0.5,
                }}
              >
                {group.label}
              </Typography>
              <List dense disablePadding>
                {group.items.map((item) => {
                  const active = (item.matches ?? [item.href]).includes(
                    pathname,
                  );
                  return (
                    <ListItemButton
                      key={item.href}
                      component={Link}
                      href={item.href}
                      onClick={onNavigate}
                      selected={active}
                      sx={{
                        borderRadius: 2,
                        mb: 0.25,
                        py: 0.9,
                        color: active
                          ? sidebarTokens.accentForeground
                          : sidebarTokens.foregroundMuted,
                        "&:hover": {
                          bgcolor: sidebarTokens.accent,
                          color: sidebarTokens.accentForeground,
                        },
                        "&.Mui-selected": {
                          bgcolor: sidebarTokens.accent,
                          color: sidebarTokens.accentForeground,
                        },
                        "&.Mui-selected:hover": {
                          bgcolor: sidebarTokens.accent,
                        },
                      }}
                    >
                      <ListItemIcon
                        sx={{ minWidth: 32, color: "inherit", opacity: 0.9 }}
                      >
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText
                        primaryTypographyProps={{
                          fontSize: "0.8rem",
                          fontWeight: 500,
                        }}
                        primary={item.label}
                      />
                      {active && (
                        <Box
                          sx={{
                            width: 6,
                            height: 6,
                            borderRadius: "50%",
                            bgcolor: sidebarTokens.primary,
                            flexShrink: 0,
                          }}
                        />
                      )}
                    </ListItemButton>
                  );
                })}
              </List>
            </Box>
          ))}
        </Stack>
      </Box>

      <Box sx={{ px: 1.5, pb: 2.5 }}>
        <Stack
          direction="row"
          spacing={1.5}
          alignItems="center"
          sx={{ px: 0.5 }}
        >
          <Avatar
            sx={{
              width: 34,
              height: 34,
              bgcolor: sidebarTokens.accent,
              color: sidebarTokens.foreground,
              fontSize: "0.75rem",
            }}
          >
            AR
          </Avatar>
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography
              variant="caption"
              fontWeight={600}
              sx={{ color: sidebarTokens.foreground, display: "block" }}
              noWrap
            >
              Developed by I.C
            </Typography>
          </Box>
          <ApartmentOutlinedIcon
            sx={{ color: sidebarTokens.foregroundMuted, fontSize: 18 }}
          />
        </Stack>
      </Box>
    </Stack>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  return (
    <Box
      sx={{
        display: "flex",
        minHeight: "100vh",
        bgcolor: "background.default",
      }}
    >
      <Box
        component="aside"
        sx={{
          display: { xs: "none", lg: "flex" },
          flexDirection: "column",
          width: DRAWER_WIDTH,
          flexShrink: 0,
          position: "sticky",
          top: 0,
          height: "100vh",
          bgcolor: sidebarTokens.background,
          borderRight: `1px solid ${sidebarTokens.border}`,
        }}
      >
        <SidebarContent pathname={pathname} />
      </Box>

      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: "block", lg: "none" },
          "& .MuiDrawer-paper": {
            width: DRAWER_WIDTH,
            bgcolor: sidebarTokens.background,
          },
        }}
      >
        <SidebarContent
          pathname={pathname}
          onNavigate={() => setMobileOpen(false)}
        />
      </Drawer>

      <Box
        sx={{ display: "flex", flexDirection: "column", flex: 1, minWidth: 0 }}
      >
        <Box
          component="header"
          sx={{
            position: "sticky",
            top: 0,
            zIndex: 10,
            borderBottom: 1,
            borderColor: "divider",
            bgcolor: "background.default",
            backdropFilter: "blur(6px)",
          }}
        >
          <Stack
            direction="row"
            alignItems="center"
            spacing={1.5}
            sx={{ minHeight: 60, px: { xs: 1.5, sm: 2.5, lg: 3 } }}
          >
            <IconButton
              onClick={() => setMobileOpen(true)}
              sx={{ display: { xs: "inline-flex", lg: "none" } }}
              aria-label="open navigation"
            >
              <MenuIcon />
            </IconButton>
            <HeaderActions />
          </Stack>
        </Box>

        <Box
          component="main"
          sx={{ flex: 1, px: { xs: 2, sm: 3, lg: 4 }, py: { xs: 3, lg: 3.5 } }}
        >
          <Box sx={{ maxWidth: 1600, mx: "auto", width: "100%" }}>
            {children}
          </Box>
        </Box>

        <Box
          component="footer"
          sx={{
            borderTop: 1,
            borderColor: "divider",
            px: { xs: 2, sm: 3, lg: 4 },
            py: 1.5,
            display: "flex",
            flexDirection: { xs: "column", sm: "row" },
            justifyContent: "space-between",
            gap: 0.5,
          }}
        >
          <Typography variant="caption" color="text.secondary">
            SCR Asset Market Risk · Solvency II workbench
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}
