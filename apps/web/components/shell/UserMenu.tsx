"use client";

import { Menu, MenuItem, Divider, ListItemText, Typography, Box } from "@mui/material";

interface UserMenuProps {
  anchorEl: HTMLElement | null;
  open: boolean;
  onClose: () => void;
}

const DEMO_NAME = "Demo Dealer";
const DEMO_EMAIL = "owner@demo.example.com";

export function UserMenu({ anchorEl, open, onClose }: UserMenuProps) {
  return (
    <Menu anchorEl={anchorEl} open={open} onClose={onClose} sx={{ mt: 1 }}>
      <Box sx={{ px: 2, py: 1.5 }}>
        <Typography variant="body2" sx={{ fontWeight: 600, color: "text.primary" }}>
          {DEMO_NAME}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {DEMO_EMAIL}
        </Typography>
      </Box>
      <Divider sx={{ my: 0.5 }} />
      <MenuItem onClick={onClose} sx={{ px: 2, py: 1, fontSize: "0.875rem" }}>
        <ListItemText primary="Profile" />
      </MenuItem>
      <MenuItem onClick={onClose} sx={{ px: 2, py: 1, fontSize: "0.875rem" }}>
        <ListItemText primary="Organization" />
      </MenuItem>
    </Menu>
  );
}
