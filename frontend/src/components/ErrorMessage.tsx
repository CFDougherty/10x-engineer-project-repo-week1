import { Alert } from '@mui/material';
import type { AlertProps } from '@mui/material';

interface ErrorMessageProps extends AlertProps {
  message: string;
  severity?: 'error' | 'warning' | 'info' | 'success';
}

export default function ErrorMessage({
  message,
  severity = 'error',
  ...props
}: ErrorMessageProps) {
  return <Alert severity={severity} {...props}>{message}</Alert>;
}