import { CircularProgress } from '@mui/material';
import { Box } from '@mui/material';
import type { CircularProgressProps } from '@mui/material';

interface LoadingSpinnerProps extends CircularProgressProps {
  size?: number | string;
  color?: 'inherit' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning';
}

export default function LoadingSpinner({
  size = 40,
  color = 'primary',
  ...props
}: LoadingSpinnerProps) {
  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
      <CircularProgress size={size} color={color} {...props} />
    </Box>
  );
}