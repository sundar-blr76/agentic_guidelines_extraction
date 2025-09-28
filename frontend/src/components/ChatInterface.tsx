import React, { useState, useRef, useEffect } from 'react';
import { Box, TextField, Button, Paper, Typography, CircularProgress, IconButton, Chip } from '@mui/material';
import { AttachFile as AttachFileIcon, Send as SendIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

interface Message {
  sender: 'user' | 'bot';
  text: string;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionStats, setSessionStats] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load or create session on mount
  useEffect(() => {
    createNewSession();
    loadSessionStats();
  }, []);

  const createNewSession = async () => {
    try {
      const response = await axios.post('http://localhost:8000/sessions', {
        context: { created_at: new Date().toISOString() }
      });
      setSessionId(response.data.session_id);
      setMessages([]); // Clear messages for new session
      console.log('Created new session:', response.data.session_id);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const loadSessionStats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/sessions');
      setSessionStats(response.data);
    } catch (error) {
      console.error('Failed to load session stats:', error);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      const file = event.target.files[0];
      setSelectedFile(file);
      setInput(file.name); // Show file name in input
    }
  };

  const handleSend = async () => {
    if (!input.trim() && !selectedFile) return;

    setIsLoading(true);
    const userMessage = input;
    setMessages(prev => [...prev, { sender: 'user', text: userMessage }]);
    setInput('');

    try {
      let responseText = '';
      let newSessionId = sessionId;
      
      if (selectedFile) {
        // File upload - use existing endpoint
        const formData = new FormData();
        formData.append('file', selectedFile);
        const response = await axios.post('http://localhost:8000/agent/ingest', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        responseText = response.data.output;
        console.info('File uploaded, response received:', responseText);
        setSelectedFile(null);
      } else {
        // Regular chat - use new session-aware endpoint
        const response = await axios.post('http://localhost:8000/agent/chat', { 
          message: userMessage,
          session_id: sessionId
        });
        responseText = response.data.output;
        newSessionId = response.data.session_id;
        
        // Update session ID if it changed (e.g., first message)
        if (newSessionId !== sessionId) {
          setSessionId(newSessionId);
        }
      }
      
      setMessages(prev => [...prev, { sender: 'bot', text: responseText }]);
      loadSessionStats(); // Refresh stats after interaction
      
    } catch (error) {
      const errorMessage = 'An error occurred. Please try again.';
      setMessages(prev => [...prev, { sender: 'bot', text: errorMessage }]);
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewSession = () => {
    createNewSession();
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: 'background.default', p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4" align="center" sx={{ flexGrow: 1 }}>
          Guideline Agent
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {sessionId && (
            <Chip 
              label={`Session: ${sessionId.substring(0, 8)}...`} 
              size="small" 
              variant="outlined" 
            />
          )}
          <IconButton onClick={handleNewSession} title="New Session">
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>
      
      {sessionStats && (
        <Box sx={{ mb: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Active sessions: {sessionStats.active_sessions} | Total: {sessionStats.total_sessions}
          </Typography>
        </Box>
      )}
      
      <Paper sx={{ flexGrow: 1, overflowY: 'auto', p: 2, mb: 2, bgcolor: 'background.paper' }}>
        {messages.length === 0 && (
          <Box sx={{ textAlign: 'center', color: 'text.secondary', mt: 4 }}>
            <Typography variant="body1">
              Welcome! Start a conversation or upload a PDF document to extract guidelines.
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Your conversation history will be maintained throughout this session.
            </Typography>
          </Box>
        )}
        {messages.map((msg, index) => (
          <Box key={index} sx={{ mb: 2, display: 'flex', justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
            <Paper
              elevation={3}
              sx={{
                p: 1.5,
                borderRadius: 2,
                bgcolor: msg.sender === 'user' ? 'primary.main' : 'white',
                color: msg.sender === 'user' ? 'primary.contrastText' : 'text.primary',
                display: 'inline-block',
                maxWidth: '80%',
              }}
            >
              {msg.sender === 'bot' ? (
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              ) : (
                <Typography variant="body1">{msg.text}</Typography>
              )}
            </Paper>
          </Box>
        ))}
      </Paper>
      <Paper elevation={3} sx={{ p: 1, display: 'flex', alignItems: 'center' }}>
        <IconButton onClick={() => fileInputRef.current?.click()} disabled={isLoading}>
          <AttachFileIcon />
        </IconButton>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type your message or upload a file..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && !isLoading && handleSend()}
          disabled={isLoading}
          sx={{ mr: 1 }}
        />
        <Button variant="contained" onClick={handleSend} disabled={isLoading}>
          {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
        </Button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </Paper>
    </Box>
  );
};

export default ChatInterface;
