"use client";

import { Menu, MenuItem, Divider, ListItemText, Typography, Box } from "@mui/material";
import { useAuth } from "../../app/AuthProvider";

interface UserMenuProps {
  anchorEl: HTMLElement | null;
  open: boolean;
  onClose: () => void;
}

export function UserMenu({ anchorEl, open, onClose }: UserMenuProps) {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    onClose();
    await logout();
  };

  return (
    <Menu
      anchorEl={anchorEl}
      open={open}
      onClose={onClose}
      sx={{ mt: 1 }}
    >
      {user && (
        <>
          <Box sx={{ px: 2, py: 1.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 600, color: "text.primary" }}>
              {user.name ?? user.email}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {user.email}
            </Typography>
          </Box>
          <Divider sx={{ my: 0.5 }} />
          <MenuItem onClick={onClose} sx={{ px: 2, py: 1, fontSize: "0.875rem" }}>
            <ListItemText primary="Profile" />
          </MenuItem>
          <MenuItem onClick={onClose} sx={{ px: 2, py: 1, fontSize: "0.875rem" }}>
            <ListItemText primary="Organization" />
          </MenuItem>
          <Divider sx={{ my: 0.5 }} />
          <MenuItem
            onClick={handleLogout}
            sx={{ px: 2, py: 1, fontSize: "0.875rem", color: "error.main" }}
          >
            <ListItemText primary="Sign out" />
          </MenuItem>
        </>
      )}
    </Menu>
  );
}
