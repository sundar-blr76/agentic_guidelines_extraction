import React from 'react';
import { CssBaseline, Container, ThemeProvider } from '@mui/material';
import ChatInterface from './components/ChatInterface';
import theme from './theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="md" sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <ChatInterface />
      </Container>
    </ThemeProvider>
  );
}

export default App;
