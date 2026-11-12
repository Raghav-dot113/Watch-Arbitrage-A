import { Drawer, Box, Typography } from '@mui/material';
import { NavLinks } from './NavLinks';

export function AppSidebar() {
  return (
    <Drawer
      variant="permanent"
      sx={{
        display: { xs: 'none', lg: 'block' },
        width: 256,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: 256,
          boxSizing: 'border-box',
          position: 'static',
          bgcolor: '#0F172A',
          borderRight: '1px solid rgba(255, 255, 255, 0.08)',
          height: '100%',
        },
      }}
    >
      <nav aria-label="Sidebar navigation" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
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
              fontSize: '0.9375rem',
            }}
          >
            Vintage Watch Intelligence
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
            ChronoArb Intelligence
          </Typography>
        </Box>
        <Box sx={{ overflow: 'auto', flex: 1, bgcolor: '#0F172A' }}>
          <NavLinks />
        </Box>
      </nav>
    </Drawer>
  );
}
