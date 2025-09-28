import React from 'react';
import { CssBaseline, Container, ThemeProvider, Box } from '@mui/material';
import ChatInterface from './components/ChatInterface';
import { createAppTheme } from './theme';
import { AppThemeProvider, useTheme } from './contexts/ThemeContext';

const AppContent: React.FC = () => {
  const { mode } = useTheme();
  const theme = createAppTheme(mode);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box 
        sx={{ 
          minHeight: '100vh',
          background: mode === 'dark' 
            ? 'linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 50%, #0f0f0f 100%)'
            : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%)',
        }}
      >
        <Container 
          maxWidth="lg" 
          sx={{ 
            height: '100vh', 
            display: 'flex', 
            flexDirection: 'column',
            py: 2
          }}
        >
          <ChatInterface />
        </Container>
      </Box>
    </ThemeProvider>
  );
};

function App() {
  return (
    <AppThemeProvider>
      <AppContent />
    </AppThemeProvider>
  );
}

export default App;
