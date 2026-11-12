"use client";

import React from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Box,
} from '@mui/material';
import { navigationConfig, isRouteActive } from '../../config/navigation';

interface NavLinksProps {
  onItemClick?: () => void;
}

export function NavLinks({ onItemClick }: NavLinksProps) {
  const pathname = usePathname();

  return (
    <List component="nav" sx={{ px: 2, py: 2 }}>
      {navigationConfig.map((item) => {
        const active = isRouteActive(pathname, item);
        const Icon = item.icon;
        const isSettings = item.label === 'Settings';

        return (
          <React.Fragment key={item.href}>
            {isSettings && (
              <Box sx={{ mt: 2, mb: 2, px: 1 }}>
                <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.08)' }} />
              </Box>
            )}
            <ListItem disablePadding sx={{ mb: 0.75 }}>
              <ListItemButton
                component={Link}
                href={item.href}
                selected={active}
                onClick={onItemClick}
                aria-current={active ? (pathname === item.href ? 'page' : 'location') : undefined}
                sx={{
                  borderRadius: 2.5,
                  py: 1,
                  px: 2,
                  color: active ? '#F59E0B' : '#94A3B8',
                  bgcolor: active ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                  transition: 'all 0.15s ease-in-out',
                  '&:hover': {
                    bgcolor: active ? 'rgba(255, 255, 255, 0.12)' : 'rgba(255, 255, 255, 0.05)',
                    color: active ? '#F59E0B' : '#F1F5F9',
                  },
                  '&.Mui-selected': {
                    bgcolor: 'rgba(255, 255, 255, 0.08)',
                    color: '#F59E0B',
                    fontWeight: 600,
                    '&:hover': {
                      bgcolor: 'rgba(255, 255, 255, 0.12)',
                    },
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 36,
                    color: active ? '#F59E0B' : '#94A3B8',
                  }}
                >
                  <Icon fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: active ? 600 : 500,
                        color: 'inherit',
                        letterSpacing: '0.01em',
                      }}
                    >
                      {item.label}
                    </Typography>
                  }
                />
              </ListItemButton>
            </ListItem>
          </React.Fragment>
        );
      })}
    </List>
  );
}
