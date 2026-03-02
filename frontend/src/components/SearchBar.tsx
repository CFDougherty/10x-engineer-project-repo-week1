import { TextField, InputAdornment, Select, MenuItem, FormControl, CircularProgress, Tooltip, IconButton } from '@mui/material';
import type { TextFieldProps } from '@mui/material';
import { Search as SearchIcon, Psychology as PsychologyIcon } from '@mui/icons-material';
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
  semantic?: boolean;
  onSemanticChange?: (semantic: boolean) => void;
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
  semantic = false,
  onSemanticChange,
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
        placeholder={semantic ? 'Semantic search (press Enter)...' : placeholder}
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
          ...(semantic && {
            '& .MuiOutlinedInput-root': {
              '& fieldset': { borderColor: 'primary.main', borderWidth: 2 },
            },
          }),
        }}
      />
      {onSemanticChange && (
        <Tooltip title={semantic ? 'Semantic search ON — click to switch to keyword search' : 'Enable semantic (AI) search'}>
          <IconButton
            size="small"
            onClick={() => onSemanticChange(!semantic)}
            sx={{
              border: 1,
              borderRadius: 1,
              borderColor: semantic ? 'primary.main' : 'divider',
              bgcolor: semantic ? 'primary.main' : 'background.paper',
              color: semantic ? 'primary.contrastText' : 'text.secondary',
              '&:hover': {
                bgcolor: semantic ? 'primary.dark' : 'action.hover',
              },
              flexShrink: 0,
              width: 40,
              height: 40,
            }}
          >
            <PsychologyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}
      {onSearchFieldChange && !semantic && (
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
