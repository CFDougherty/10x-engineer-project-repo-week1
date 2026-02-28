import { useState, useMemo } from 'react';
import { usePrompts } from '../contexts/PromptsContext';
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
import VersionHistoryDialog from '../components/VersionHistoryDialog';

export default function PromptsPage() {
  const { prompts, loading, error, create, update, remove, refetch } = usePrompts();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [selectedCollection, setSelectedCollection] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [historyPromptId, setHistoryPromptId] = useState<string | null>(null);
  const { collections } = useCollections();

  const filteredPrompts = useMemo(() => {
    let result = prompts;
    if (selectedCollection === '__none__') {
      result = result.filter(p => !p.collection_id);
    } else if (selectedCollection) {
      result = result.filter(p => p.collection_id === selectedCollection);
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(p => {
        if (filter === 'title') return p.title.toLowerCase().includes(q);
        if (filter === 'content') return p.content.toLowerCase().includes(q);
        return (
          p.title.toLowerCase().includes(q) ||
          p.content.toLowerCase().includes(q) ||
          p.description?.toLowerCase().includes(q) ||
          p.tags?.some((t: string) => t.toLowerCase().includes(q))
        );
      });
    }
    return result;
  }, [prompts, searchQuery, filter, selectedCollection]);

  const handleSearch = async () => {
    setSearchLoading(true);
    try {
      await refetch();
    } finally {
      setSearchLoading(false);
    }
  };

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

  const handleViewHistory = (promptId: string) => {
    setHistoryPromptId(promptId);
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
      <Box display="flex" flexDirection={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'stretch', sm: 'center' }} mb={4} gap={2}>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4" gutterBottom>Prompts</Typography>
          <Box display="flex" alignItems="center" gap={2} mb={2} flexWrap="wrap">
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              onSearch={handleSearch}
              searchField={filter}
              onSearchFieldChange={setFilter}
              placeholder="Search prompts..."
              loading={searchLoading}
              sx={{ flexGrow: 1 }}
            />
            <FormControl sx={{ minWidth: { xs: '100%', sm: 200 } }}>
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
                <MenuItem value="__none__">Not in any collection</MenuItem>
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
          sx={{ ml: { xs: 0, sm: 2 }, alignSelf: { xs: 'flex-start', sm: 'center' }, flexShrink: 0 }}
        >
          New Prompt
        </Button>
      </Box>

      {/* Prompt Creation Dialog */}
      <PromptFormDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        mode="create"
        onSubmit={async (promptData) => {
          await create(promptData);
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

      <VersionHistoryDialog
        open={historyPromptId !== null}
        onClose={() => setHistoryPromptId(null)}
        promptId={historyPromptId ?? ''}
        onRestored={refetch}
      />

      {filteredPrompts.length === 0 ? (
        <Alert severity="info">No prompts found. Create your first prompt!</Alert>
      ) : (
        <Grid container spacing={3}>
          {filteredPrompts.map((prompt) => (
            // @ts-expect-error - prompt type has missing properties
            <Grid item xs={12} sm={6} md={4} key={prompt.id} sx={{ display: 'flex' }}>
              <PromptCard
                prompt={prompt}
                collectionName={collections.find(c => c.id === prompt.collection_id)?.name}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onViewHistory={handleViewHistory}
              />
            </Grid>
          ))}
        </Grid>
      )}
    </div>
  );
}