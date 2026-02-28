import { useState, useEffect } from 'react';
import { usePrompts } from '../hooks/usePrompts';
import { useCollections } from '../contexts/CollectionsContext';
import type { Prompt } from '../types/prompt';
import {
  Typography,
  CircularProgress,
  Alert,
  Box,
  MenuItem,
  FormControl,
  InputLabel,
  Select
} from '@mui/material';
import { Grid } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import PromptFormDialog from '../components/PromptCreationDialog';
import SearchBar from '../components/SearchBar';
import Button from '../components/Button';
import PromptCard from '../components/PromptCard';

export default function PromptsPage() {
  const { prompts, loading, error, update, remove, refetch } = usePrompts();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [selectedCollection, setSelectedCollection] = useState('');
  const { collections } = useCollections();

  // Apply search and filter
  useEffect(() => {
    const params: any = {};
    if (searchQuery) {
      params.search = searchQuery;
      params.filter = filter;
    }
    if (selectedCollection) {
      params.collectionId = selectedCollection;
    }
    if (Object.keys(params).length > 0) {
      refetch(params);
    } else {
      refetch();
    }
  }, [searchQuery, filter, selectedCollection, refetch]);

  const handleOpen = () => {
    setCreateDialogOpen(true);
  };

  const handleEdit = (promptId: string) => {
    const prompt = prompts.find(p => p.id === promptId);
    if (prompt) {
      setEditingPrompt(prompt);
      setEditDialogOpen(true);
    }
  };

  const handleCloseEdit = () => {
    setEditDialogOpen(false);
  };

  const handleEditSubmit = async (promptData: {
    title: string;
    content: string;
    description?: string;
    tags: string[];
    collection_id?: string;
  }) => {
    if (!editingPrompt) return;
    try {
      await update(editingPrompt.id, promptData);
    } catch (err) {
      console.error('Error saving prompt:', err);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await remove(id);
    } catch (err) {
      console.error('Error deleting prompt:', err);
    }
  };

  if (loading && prompts.length === 0) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <div>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4" gutterBottom>Prompts</Typography>
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              searchField={filter}
              onSearchFieldChange={setFilter}
              placeholder="Search prompts..."
              sx={{ flexGrow: 1 }}
            />
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Filter by Collection</InputLabel>
              <Select
                value={selectedCollection}
                label="Filter by Collection"
                onChange={(e) => setSelectedCollection(e.target.value)}
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
                <MenuItem value="">All Collections</MenuItem>
                {collections.map((collection) => (
                  <MenuItem key={collection.id} value={collection.id}>
                    {collection.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleOpen}
          sx={{ ml: 2 }}
        >
          New Prompt
        </Button>
      </Box>

      {/* Prompt Creation Dialog */}
      <PromptFormDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        mode="create"
        onSubmit={async () => {
          await refetch();
        }}
        onPromptCreated={refetch}
      />

      {/* Edit Prompt Dialog */}
      <PromptFormDialog
        open={editDialogOpen}
        onClose={handleCloseEdit}
        mode="edit"
        initialData={editingPrompt || undefined}
        onSubmit={handleEditSubmit}
      />

      {prompts.length === 0 ? (
        <Alert severity="info">No prompts found. Create your first prompt!</Alert>
      ) : (
        <Grid container spacing={3}>
          {prompts.map((prompt) => (
            // @ts-expect-error - prompt type has missing properties
            <Grid item xs={12} sm={6} md={4} key={prompt.id} sx={{ display: 'flex' }}>
              <PromptCard
                prompt={prompt}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            </Grid>
          ))}
        </Grid>
      )}
    </div>
  );
}