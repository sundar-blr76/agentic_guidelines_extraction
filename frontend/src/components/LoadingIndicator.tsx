import React from 'react';
import { Box, CircularProgress, Typography, keyframes } from '@mui/material';
import { styled } from '@mui/material/styles';

const pulse = keyframes`
  0% {
    transform: scale(1);
    opacity: 0.7;
  }
  50% {
    transform: scale(1.1);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0.7;
  }
`;

const PulsingBox = styled(Box)(({ theme }) => ({
  animation: `${pulse} 2s ease-in-out infinite`,
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(2),
  padding: theme.spacing(2),
  borderRadius: theme.spacing(2),
  backgroundColor: theme.palette.mode === 'dark' ? 'rgba(187, 134, 252, 0.1)' : 'rgba(99, 102, 241, 0.1)',
  border: `1px solid ${theme.palette.divider}`,
}));

interface LoadingIndicatorProps {
  message?: string;
}

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ 
  message = "Processing..." 
}) => {
  return (
    <PulsingBox>
      <CircularProgress size={24} />
      <Typography variant="body2" color="text.secondary">
        {message}
      </Typography>
    </PulsingBox>
  );
};

export default LoadingIndicator;