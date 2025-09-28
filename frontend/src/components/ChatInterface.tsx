import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Paper, 
  Typography, 
  CircularProgress, 
  IconButton, 
  Chip,
  Fade,
  Slide,
  Zoom,
  Alert,
  LinearProgress,
  Tooltip,
  Divider,
  Avatar,
  Card,
  CardContent
} from '@mui/material';
import { 
  AttachFile as AttachFileIcon, 
  Send as SendIcon, 
  Refresh as RefreshIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Description as DocumentIcon,
  Analytics as StatsIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { useTheme } from '../contexts/ThemeContext';

interface Message {
  sender: 'user' | 'bot';
  text: string;
  timestamp: Date;
}

const AnimatedPaper = styled(Paper)(({ theme }) => ({
  transition: 'all 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[8],
  },
}));

const MessageBubble = styled(Paper, {
  shouldForwardProp: (prop) => prop !== 'isUser',
})<{ isUser: boolean }>(({ theme, isUser }) => ({
  maxWidth: '80%',
  padding: theme.spacing(1.5, 2),
  borderRadius: isUser ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
  backgroundColor: isUser 
    ? theme.palette.primary.main 
    : theme.palette.background.paper,
  color: isUser 
    ? theme.palette.primary.contrastText 
    : theme.palette.text.primary,
  border: isUser ? 'none' : `1px solid ${theme.palette.divider}`,
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    width: 0,
    height: 0,
    border: '8px solid transparent',
    ...(isUser ? {
      right: -8,
      bottom: 8,
      borderLeftColor: theme.palette.primary.main,
    } : {
      left: -8,
      bottom: 8,
      borderRightColor: theme.palette.background.paper,
    }),
  },
}));

const StatsCard = styled(Card)(({ theme }) => ({
  background: theme.palette.mode === 'dark' 
    ? 'linear-gradient(135deg, rgba(187, 134, 252, 0.1) 0%, rgba(3, 218, 198, 0.1) 100%)'
    : 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%)',
  border: `1px solid ${theme.palette.divider}`,
}));

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionStats, setSessionStats] = useState<any>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { mode, toggleColorMode } = useTheme();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      setMessages([]);
      setSuccessMessage('New session created successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error) {
      setErrorMessage('Failed to create session');
      setTimeout(() => setErrorMessage(null), 3000);
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
      if (file.type !== 'application/pdf') {
        setErrorMessage('Please select a PDF file');
        setTimeout(() => setErrorMessage(null), 3000);
        return;
      }
      setSelectedFile(file);
      setInput(`📄 ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`);
    }
  };

  const handleSend = async () => {
    if (!input.trim() && !selectedFile) return;

    setIsLoading(true);
    const userMessage = selectedFile ? `Upload: ${selectedFile.name}` : input;
    const newMessage: Message = { 
      sender: 'user', 
      text: userMessage, 
      timestamp: new Date() 
    };
    setMessages(prev => [...prev, newMessage]);
    setInput('');

    try {
      let responseText = '';
      let newSessionId = sessionId;
      
      if (selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        // Simulate upload progress
        setUploadProgress(0);
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => Math.min(prev + 10, 90));
        }, 200);

        const response = await axios.post('http://localhost:8000/agent/ingest', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        
        clearInterval(progressInterval);
        setUploadProgress(100);
        
        responseText = response.data.message || 'Document processed successfully';
        setSelectedFile(null);
        setTimeout(() => setUploadProgress(0), 1000);
      } else {
        const response = await axios.post('http://localhost:8000/agent/chat', { 
          message: input,
          session_id: sessionId
        });
        responseText = response.data.response;
        newSessionId = response.data.session_id;
        
        if (newSessionId !== sessionId) {
          setSessionId(newSessionId);
        }
      }
      
      const botResponse: Message = {
        sender: 'bot',
        text: responseText,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, botResponse]);
      loadSessionStats();
      
    } catch (error) {
      const errorMessage = 'An error occurred. Please try again.';
      const errorResponse: Message = {
        sender: 'bot',
        text: errorMessage,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorResponse]);
      setErrorMessage('Failed to process request');
      setTimeout(() => setErrorMessage(null), 3000);
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewSession = () => {
    createNewSession();
  };

  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
      {/* Header */}
      <AnimatedPaper elevation={2} sx={{ p: 3, mb: 2, borderRadius: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <BotIcon />
            </Avatar>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                Guideline Agent
              </Typography>
              <Typography variant="body2" color="text.secondary">
                AI-powered document analysis and chat
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Tooltip title={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}>
              <IconButton onClick={toggleColorMode} sx={{ borderRadius: 2 }}>
                {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
              </IconButton>
            </Tooltip>
            {sessionId && (
              <Tooltip title="Current session">
                <Chip 
                  icon={<StatsIcon />}
                  label={`${sessionId.substring(0, 8)}...`} 
                  variant="outlined"
                  sx={{ borderRadius: 2 }}
                />
              </Tooltip>
            )}
            <Tooltip title="Start new session">
              <IconButton onClick={handleNewSession} sx={{ borderRadius: 2 }}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </AnimatedPaper>

      {/* Session Stats */}
      {sessionStats && (
        <Fade in={true} timeout={500}>
          <StatsCard sx={{ mb: 2 }}>
            <CardContent sx={{ py: 1.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Session Statistics
                </Typography>
                <Box sx={{ display: 'flex', gap: 3 }}>
                  <Typography variant="body2">
                    <strong>Active:</strong> {sessionStats.active_sessions}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Total:</strong> {sessionStats.total_sessions}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </StatsCard>
        </Fade>
      )}

      {/* Alert Messages */}
      {successMessage && (
        <Slide direction="down" in={Boolean(successMessage)} mountOnEnter unmountOnExit>
          <Alert severity="success" sx={{ mb: 2, borderRadius: 2 }}>
            {successMessage}
          </Alert>
        </Slide>
      )}
      
      {errorMessage && (
        <Slide direction="down" in={Boolean(errorMessage)} mountOnEnter unmountOnExit>
          <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
            {errorMessage}
          </Alert>
        </Slide>
      )}

      {/* Upload Progress */}
      {uploadProgress > 0 && uploadProgress < 100 && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress 
            variant="determinate" 
            value={uploadProgress} 
            sx={{ borderRadius: 1, height: 8 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            Uploading document... {uploadProgress}%
          </Typography>
        </Box>
      )}

      {/* Chat Messages */}
      <AnimatedPaper 
        elevation={1} 
        sx={{ 
          flexGrow: 1, 
          overflowY: 'auto', 
          p: 2, 
          mb: 2, 
          borderRadius: 3,
          position: 'relative',
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'rgba(0,0,0,0.1)',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'rgba(0,0,0,0.3)',
            borderRadius: '4px',
          },
        }}
      >
        {messages.length === 0 && (
          <Fade in={true} timeout={1000}>
            <Box sx={{ 
              textAlign: 'center', 
              color: 'text.secondary', 
              mt: 4,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 2
            }}>
              <Avatar sx={{ bgcolor: 'primary.main', width: 64, height: 64 }}>
                <BotIcon sx={{ fontSize: 32 }} />
              </Avatar>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Welcome to Guideline Agent!
              </Typography>
              <Typography variant="body1" sx={{ maxWidth: 400 }}>
                Start a conversation or upload a PDF document to extract guidelines.
                Your conversation history will be maintained throughout this session.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                <Chip icon={<DocumentIcon />} label="Upload PDF" variant="outlined" />
                <Chip icon={<BotIcon />} label="Ask Questions" variant="outlined" />
              </Box>
            </Box>
          </Fade>
        )}
        
        {messages.map((msg, index) => (
          <Zoom key={index} in={true} timeout={300} style={{ transitionDelay: `${index * 100}ms` }}>
            <Box sx={{ 
              mb: 3, 
              display: 'flex', 
              justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              alignItems: 'flex-end',
              gap: 1
            }}>
              {msg.sender === 'bot' && (
                <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                  <BotIcon fontSize="small" />
                </Avatar>
              )}
              
              <Box sx={{ maxWidth: '80%' }}>
                <MessageBubble elevation={2} isUser={msg.sender === 'user'}>
                  {msg.sender === 'bot' ? (
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  ) : (
                    <Typography variant="body1">{msg.text}</Typography>
                  )}
                </MessageBubble>
                <Typography 
                  variant="caption" 
                  color="text.secondary" 
                  sx={{ 
                    display: 'block', 
                    textAlign: msg.sender === 'user' ? 'right' : 'left',
                    mt: 0.5,
                    ml: msg.sender === 'bot' ? 1 : 0,
                    mr: msg.sender === 'user' ? 1 : 0
                  }}
                >
                  {formatTime(msg.timestamp)}
                </Typography>
              </Box>
              
              {msg.sender === 'user' && (
                <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                  <PersonIcon fontSize="small" />
                </Avatar>
              )}
            </Box>
          </Zoom>
        ))}
        <div ref={messagesEndRef} />
      </AnimatedPaper>

      {/* Input Area */}
      <AnimatedPaper elevation={3} sx={{ p: 2, borderRadius: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Attach PDF document">
            <IconButton 
              onClick={() => fileInputRef.current?.click()} 
              disabled={isLoading}
              sx={{ borderRadius: 2 }}
            >
              <AttachFileIcon />
            </IconButton>
          </Tooltip>
          
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Type your message or upload a PDF file..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && !isLoading && handleSend()}
            disabled={isLoading}
            multiline
            maxRows={4}
            sx={{ 
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
              }
            }}
          />
          
          <Tooltip title="Send message">
            <span>
              <Button 
                variant="contained" 
                onClick={handleSend} 
                disabled={isLoading || (!input.trim() && !selectedFile)}
                sx={{ 
                  minWidth: 56, 
                  height: 56, 
                  borderRadius: 3,
                  boxShadow: 'none'
                }}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  <SendIcon />
                )}
              </Button>
            </span>
          </Tooltip>
          
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf"
            style={{ display: 'none' }}
          />
        </Box>
      </AnimatedPaper>
    </Box>
  );
};

export default ChatInterface;
