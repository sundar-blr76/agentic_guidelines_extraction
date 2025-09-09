import React, { useState, useRef } from 'react';
import { Box, TextField, Button, Paper, Typography, CircularProgress, IconButton } from '@mui/material';
import { AttachFile as AttachFileIcon, Send as SendIcon } from '@mui/icons-material';
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
  const fileInputRef = useRef<HTMLInputElement>(null);

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
      if (selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        const response = await axios.post('http://172.24.160.231:8000/agent/ingest', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        responseText = response.data.output; // Extract the output string
        setSelectedFile(null); // Clear file after sending
      } else {
        const response = await axios.post('http://172.24.160.231:8000/agent/query', { input: userMessage });
        responseText = response.data.output; // Extract the output string
      }
      setMessages(prev => [...prev, { sender: 'bot', text: responseText }]);
    } catch (error) {
      const errorMessage = 'An error occurred. Please try again.';
      setMessages(prev => [...prev, { sender: 'bot', text: errorMessage }]);
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: 'background.default', p: 2 }}>
      <Typography variant="h4" align="center" gutterBottom>
        Guideline Agent
      </Typography>
      <Paper sx={{ flexGrow: 1, overflowY: 'auto', p: 2, mb: 2, bgcolor: 'background.paper' }}>
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
