import { createTheme } from '@mui/material/styles';
import {
  semanticColors,
  darkSemanticColors,
  typography,
  spacing,
  radii,
  breakpoints,
} from '@chronoarb/design-tokens';

declare module '@mui/material/styles' {
  interface Palette {
    opportunityPositive: Palette['primary'];
    opportunityRisk: Palette['primary'];
  }
  interface PaletteOptions {
    opportunityPositive?: PaletteOptions['primary'];
    opportunityRisk?: PaletteOptions['primary'];
  }
}

declare module '@mui/material/styles' {
  interface BreakpointOverrides {
    xs: true;
    sm: true;
    md: true;
    lg: true;
    xl: true;
    '2xl': true;
  }
}

export const theme = createTheme({
  cssVariables: {
    colorSchemeSelector: 'class',
  },
  palette: {
    mode: 'light',
    background: {
      default: '#F8FAFC',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#0F172A',
      secondary: '#64748B',
    },
    divider: '#E2E8F0',
    primary: {
      main: '#2563EB',
      light: '#3B82F6',
      dark: '#1D4ED8',
      contrastText: '#FFFFFF',
    },
    success: {
      main: '#16A34A',
      light: '#22C55E',
      dark: '#15803D',
      contrastText: '#FFFFFF',
    },
    warning: {
      main: '#F59E0B',
      light: '#FBBF24',
      dark: '#D97706',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#DC2626',
      light: '#EF4444',
      dark: '#B91C1C',
      contrastText: '#FFFFFF',
    },
    info: {
      main: '#0284C7',
      light: '#38BDF8',
      dark: '#0369A1',
      contrastText: '#FFFFFF',
    },
    opportunityPositive: {
      main: '#16A34A',
    },
    opportunityRisk: {
      main: '#DC2626',
    },
    action: {
      active: '#64748B',
      hover: '#F1F5F9',
      selected: '#E2E8F0',
      disabled: '#CBD5E1',
      disabledBackground: '#F1F5F9',
      focus: '#94A3B8',
    },
  },
  typography: {
    fontFamily: typography.fontFamily,
    h1: typography.h1,
    h2: typography.h2,
    h3: typography.h3,
    body1: typography.body1,
    body2: typography.body2,
    caption: typography.caption,
    overline: typography.overline,
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  spacing: spacing,
  shape: {
    borderRadius: radii.md,
  },
  breakpoints: breakpoints,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#F8FAFC',
          color: '#0F172A',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          borderRadius: 10,
          fontWeight: 600,
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFFFFF',
          borderColor: '#E2E8F0',
          borderRadius: 16,
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#FFFFFF',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#0F172A',
          borderRight: '1px solid #1E293B',
          color: '#FFFFFF',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFFFFF',
          borderBottom: '1px solid #E2E8F0',
          color: '#0F172A',
          boxShadow: 'none',
        },
      },
    },
    MuiToolbar: {
      styleOverrides: {
        root: {
          minHeight: 64,
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: '#E2E8F0',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
          borderRadius: 8,
        },
      },
    },
  },
});
