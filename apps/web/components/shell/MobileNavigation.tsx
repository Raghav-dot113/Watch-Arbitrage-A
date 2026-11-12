"use client";

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { AppBar, Toolbar, IconButton, Typography, Drawer, Box } from '@mui/material';
import MenuOutlinedIcon from '@mui/icons-material/MenuOutlined';
import { NavLinks } from './NavLinks';
import { navigationConfig, isRouteActive } from '../../config/navigation';

export function MobileNavigation() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const currentNav = navigationConfig.find(item => isRouteActive(pathname, item));
  const title = currentNav ? currentNav.label : 'ChronoArb';

  return (
    <>
      <AppBar
        position="static"
        elevation={0}
        sx={{
          display: { xs: 'block', lg: 'none' },
          borderBottom: '1px solid',
          borderColor: 'divider',
          boxShadow: 'none',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="Open navigation"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            <MenuOutlinedIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold' }}>
            {title}
          </Typography>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: { xs: 'block', lg: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: 256,
            bgcolor: '#0F172A',
            borderRight: '1px solid rgba(255, 255, 255, 0.08)',
          },
        }}
      >
        <nav aria-label="Mobile navigation" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <Box
            sx={{
              px: 3,
              py: 2.5,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              minHeight: 64,
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <Typography
              sx={{
                fontWeight: 700,
                letterSpacing: '-0.01em',
                lineHeight: 1.2,
                color: '#F8FAFC',
                fontSize: '1.125rem',
              }}
            >
              ChronoArb
            </Typography>
            <Typography
              variant="caption"
              sx={{
                fontWeight: 600,
                letterSpacing: '0.08em',
                mt: 0.5,
                color: '#F59E0B',
                fontSize: '0.625rem',
                textTransform: 'uppercase',
              }}
            >
              Watch Arbitrage Intelligence
            </Typography>
          </Box>
          <Box sx={{ overflow: 'auto', flex: 1, bgcolor: '#0F172A' }}>
            <NavLinks onItemClick={() => setMobileOpen(false)} />
          </Box>
        </nav>
      </Drawer>
    </>
  );
}
