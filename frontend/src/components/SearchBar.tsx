import { TextField, InputAdornment, Select, MenuItem, FormControl, CircularProgress, Tooltip, IconButton } from '@mui/material';
import type { TextFieldProps } from '@mui/material';
import { Search as SearchIcon, Psychology as PsychologyIcon, Clear as ClearIcon, Abc as AbcIcon, ManageSearch as ManageSearchIcon } from '@mui/icons-material';
import { useRef, useEffect } from 'react';

type SearchMode = 'keyword' | 'fuzzy' | 'semantic';

interface SearchBarProps extends Omit<TextFieldProps, 'onChange' | 'value'> {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  size?: 'small' | 'medium';
  searchField?: string;
  onSearchFieldChange?: (field: string) => void;
  onSearch?: () => void;
  onClear?: () => void;
  loading?: boolean;
  searchMode?: SearchMode;
  onSearchModeChange?: (mode: SearchMode) => void;
}

export default function SearchBar({
  value,
  onChange,
  placeholder = 'Search...',
  size = 'small',
  searchField = 'all',
  onSearchFieldChange,
  onSearch,
  onClear,
  loading = false,
  searchMode = 'fuzzy',
  onSearchModeChange,
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

  const modeButtonSx = (mode: SearchMode) => ({
    border: 1,
    borderRadius: 1,
    borderColor: searchMode === mode ? 'primary.main' : 'divider',
    bgcolor: searchMode === mode ? 'primary.main' : 'background.paper',
    color: searchMode === mode ? 'primary.contrastText' : 'text.secondary',
    '&:hover': {
      bgcolor: searchMode === mode ? 'primary.dark' : 'action.hover',
    },
    flexShrink: 0,
    width: 40,
    height: 40,
  });

  return (
    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
      <TextField
        fullWidth
        variant="outlined"
        size={size}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={searchMode === 'semantic' ? 'Semantic search (press Enter)...' : placeholder}
        inputRef={inputRef}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              {loading ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
            </InputAdornment>
          ),
          endAdornment: value ? (
            <InputAdornment position="end">
              <IconButton size="small" onClick={onClear} edge="end">
                <ClearIcon fontSize="small" />
              </IconButton>
            </InputAdornment>
          ) : undefined,
        }}
        sx={{
          backgroundColor: 'background.paper',
          borderRadius: 1,
          ...(searchMode === 'semantic' && {
            '& .MuiOutlinedInput-root': {
              '& fieldset': { borderColor: 'primary.main', borderWidth: 2 },
            },
          }),
        }}
      />
      {onSearchModeChange && (
        <>
          <Tooltip title="Keyword search — exact text matching">
            <IconButton size="small" onClick={() => onSearchModeChange('keyword')} sx={modeButtonSx('keyword')}>
              <AbcIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Fuzzy search — approximate text matching">
            <IconButton size="small" onClick={() => onSearchModeChange('fuzzy')} sx={modeButtonSx('fuzzy')}>
              <ManageSearchIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Semantic search — search by meaning (AI)">
            <IconButton size="small" onClick={() => onSearchModeChange('semantic')} sx={modeButtonSx('semantic')}>
              <PsychologyIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </>
      )}
      {onSearchFieldChange && (
        <Tooltip title={searchMode === 'semantic' ? 'Field filter is not available in semantic search' : ''}>
          <FormControl size="small" sx={{ minWidth: 120 }} disabled={searchMode === 'semantic'}>
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
        </Tooltip>
      )}
    </div>
  );
}
