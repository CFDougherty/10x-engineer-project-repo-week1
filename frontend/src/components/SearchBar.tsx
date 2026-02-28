import { TextField, InputAdornment, Select, MenuItem, FormControl, CircularProgress } from '@mui/material';
import type { TextFieldProps } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { useRef, useEffect } from 'react';

interface SearchBarProps extends Omit<TextFieldProps, 'onChange' | 'value'> {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  size?: 'small' | 'medium';
  searchField?: string;
  onSearchFieldChange?: (field: string) => void;
  onSearch?: () => void;
  loading?: boolean;
}

export default function SearchBar({
  value,
  onChange,
  placeholder = 'Search...',
  size = 'small',
  searchField = 'all',
  onSearchFieldChange,
  onSearch,
  loading = false,
}: SearchBarProps) {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.value);
  };

  const handleSearchFieldChange = (event: any) => {
    if (onSearchFieldChange) {
      onSearchFieldChange(event.target.value);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && onSearch) {
      onSearch();
    }
  };

  const inputRef = useRef<HTMLInputElement>(null);

  // Maintain focus when typing, even if search results are empty
  useEffect(() => {
    if (inputRef.current && value !== '') {
      inputRef.current.focus();
    }
  }, [value]);

  return (
    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
      <TextField
        fullWidth
        variant="outlined"
        size={size}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        inputRef={inputRef}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              {loading ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
            </InputAdornment>
          ),
        }}
        sx={{
          backgroundColor: 'background.paper',
          borderRadius: 1,
        }}
      />
      {onSearchFieldChange && (
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <Select
            value={searchField}
            onChange={handleSearchFieldChange}
            displayEmpty
            sx={{
              backgroundColor: 'background.paper',
              borderRadius: 1,
              '& .MuiOutlinedInput-root': {
                '& fieldset': {
                  borderColor: 'rgba(0, 0, 0, 0.23)',
                },
              },
            }}
            MenuProps={{
              PaperProps: {
                sx: {
                  bgcolor: 'background.paper',
                  '& .MuiMenuItem-root': {
                    color: 'text.primary'
                  }
                }
              }
            }}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="title">Title</MenuItem>
            <MenuItem value="content">Content</MenuItem>
            <MenuItem value="description">Description</MenuItem>
            <MenuItem value="tags">Tags</MenuItem>
            <MenuItem value="collection">Collection</MenuItem>
          </Select>
        </FormControl>
      )}
    </div>
  );
}