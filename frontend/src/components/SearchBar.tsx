import { TextField, InputAdornment } from '@mui/material';
import type { TextFieldProps } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { useRef, useEffect } from 'react';

interface SearchBarProps extends Omit<TextFieldProps, 'onChange' | 'value'> {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  size?: 'small' | 'medium';
}

export default function SearchBar({
  value,
  onChange,
  placeholder = 'Search...',
  size = 'small',
}: SearchBarProps) {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.value);
  };

  const inputRef = useRef<HTMLInputElement>(null);

  // Maintain focus when typing, even if search results are empty
  useEffect(() => {
    if (inputRef.current && value !== '') {
      inputRef.current.focus();
    }
  }, [value]);

  return (
    <TextField
      fullWidth
      variant="outlined"
      size={size}
      value={value}
      onChange={handleChange}
      placeholder={placeholder}
      inputRef={inputRef}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon />
          </InputAdornment>
        ),
      }}
      sx={{
        backgroundColor: 'background.paper',
        borderRadius: 1,
      }}
    />
  );
}
