"use client";

import { useState } from "react";
import { AppBar, Toolbar, Box, Avatar } from "@mui/material";
import { AppSidebar } from "./AppSidebar";
import { MobileNavigation } from "./MobileNavigation";
import { UserMenu } from "./UserMenu";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
    setUserMenuOpen(true);
  };

  const handleUserMenuClose = () => {
    setUserMenuOpen(false);
    setAnchorEl(null);
  };

  return (
    <div className="flex flex-col lg:flex-row h-[100dvh] overflow-hidden">
      {/* Skip to main content link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:z-50 focus:p-4 focus:font-bold"
        style={{
          backgroundColor: "var(--mui-palette-background-paper)",
          color: "var(--mui-palette-primary-main)",
        }}
      >
        Skip to main content
      </a>

      {/* Desktop sidebar */}
      <AppSidebar />

      {/* Main Column */}
      <div className="flex flex-col flex-1 min-w-0 min-h-0 bg-[#F8FAFC]">
        {/* Desktop AppBar */}
        <AppBar
          position="static"
          elevation={0}
          sx={{
            display: { xs: "none", lg: "block" },
            bgcolor: "#FFFFFF",
            borderBottom: "1px solid",
            borderColor: "divider",
            boxShadow: "none",
          }}
        >
          <Toolbar>
            <Box sx={{ flexGrow: 1 }} />
            <Avatar
              sx={{
                width: 34,
                height: 34,
                fontSize: 15,
                fontWeight: 600,
                bgcolor: "#0F172A",
                color: "#F8FAFC",
                cursor: "pointer",
                border: "1px solid #E2E8F0",
                "&:hover": { bgcolor: "#1E293B" },
              }}
              onClick={handleUserMenuOpen}
              aria-label="Open user menu"
            >
              U
            </Avatar>
            <UserMenu
              anchorEl={anchorEl}
              open={userMenuOpen}
              onClose={handleUserMenuClose}
            />
          </Toolbar>
        </AppBar>

        {/* Mobile Navigation (includes AppBar) */}
        <MobileNavigation />

        {/* Main Content Area */}
        <main
          id="main-content"
          className="flex-1 min-h-0 overflow-y-auto"
          tabIndex={-1}
          style={{ outline: "none" }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
