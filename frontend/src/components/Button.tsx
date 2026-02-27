import { Button as MuiButton } from '@mui/material';
import type { ButtonProps as MuiButtonProps } from '@mui/material';

interface ButtonProps extends MuiButtonProps {
  children: React.ReactNode;
  variant?: 'text' | 'outlined' | 'contained';
  color?: 'inherit' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning';
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
}

export default function Button({
  children,
  variant = 'contained',
  color = 'primary',
  size = 'medium',
  onClick,
  ...props
}: ButtonProps) {
  return (
    <MuiButton
      variant={variant}
      color={color}
      size={size}
      onClick={onClick}
      {...props}
    >
      {children}
    </MuiButton>
  );
}