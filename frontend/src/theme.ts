import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // A professional blue
    },
    secondary: {
      main: '#607d8b', // A complementary grey
    },
    background: {
      default: '#f4f6f8', // A light grey background
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Inter", sans-serif',
    h4: {
      fontWeight: 500,
      color: '#263238', // Darker grey for headings
    },
    body1: {
      fontSize: '1rem',
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0px 2px 4px -1px rgba(0,0,0,0.06), 0px 4px 5px 0px rgba(0,0,0,0.06), 0px 1px 10px 0px rgba(0,0,0,0.08)',
        },
      },
    },
  },
});

export default theme;
