import { useState, useEffect } from 'react';
import { usePrompts } from '../hooks/usePrompts';
import { useCollections } from '../hooks/useCollections';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  CircularProgress,
  Alert,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Box,
  IconButton,
  MenuItem,
  FormControl,
  InputLabel,
  Select
} from '@mui/material';
import { Grid } from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import PromptCreationDialog from '../components/PromptCreationDialog';
import SearchBar from '../components/SearchBar';
import Button from '../components/Button';
import { formatDateTime } from '../utils/dateUtils';

export default function PromptsPage() {
  const { prompts, loading, error, update, remove, refetch } = usePrompts();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<any>(null);
  const [editFormData, setEditFormData] = useState({
    title: '',
    content: '',
    tags: '',
    collectionId: '',
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCollection, setSelectedCollection] = useState('');
  const { collections } = useCollections();
  const navigate = useNavigate();

  // Apply search and filter
  useEffect(() => {
    const params: any = {};
    if (searchQuery) {
      params.search = searchQuery;
    }
    if (selectedCollection) {
      params.collectionId = selectedCollection;
    }
    if (Object.keys(params).length > 0) {
      refetch(params);
    } else {
      refetch();
    }
  }, [searchQuery, selectedCollection, refetch]);

  const handleOpen = () => {
    setCreateDialogOpen(true);
  };

  const handleEdit = (prompt: any) => {
    setEditingPrompt(prompt);
    setEditFormData({
      title: prompt.title,
      content: prompt.content,
      tags: prompt.tags?.join(', ') || '',
      collectionId: prompt.collection_id || '',
    });
    setEditDialogOpen(true);
  };

  const handleCloseEdit = () => {
    setEditDialogOpen(false);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const tagsArray = editFormData.tags.split(',').map((tag: string) => tag.trim()).filter(Boolean);
      const promptData = {
        title: editFormData.title,
        content: editFormData.content,
        tags: tagsArray,
        collection_id: editFormData.collectionId || undefined,
      };
      await update(editingPrompt.id, promptData);
      handleCloseEdit();
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
      <PromptCreationDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onPromptCreated={refetch}
      />

      {/* Edit Prompt Dialog */}
      <Dialog open={editDialogOpen} onClose={handleCloseEdit}>
        <form onSubmit={handleEditSubmit}>
          <DialogTitle>Edit Prompt</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Title"
              fullWidth
              value={editFormData.title}
              onChange={(e) => setEditFormData({...editFormData, title: e.target.value})}
              required
            />
            <TextField
              margin="dense"
              label="Content"
              fullWidth
              multiline
              rows={4}
              value={editFormData.content}
              onChange={(e) => setEditFormData({...editFormData, content: e.target.value})}
              required
            />
            <TextField
              margin="dense"
              label="Tags (comma separated)"
              fullWidth
              value={editFormData.tags}
              onChange={(e) => setEditFormData({...editFormData, tags: e.target.value})}
            />
            <TextField
              select
              margin="dense"
              label="Collection"
              fullWidth
              value={editFormData.collectionId}
              onChange={(e) => setEditFormData({...editFormData, collectionId: e.target.value})}
            >
              <MenuItem value="">None (no collection)</MenuItem>
              {collections.map((collection) => (
                <MenuItem key={collection.id} value={collection.id}>
                  {collection.name}
                </MenuItem>
              ))}
            </TextField>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseEdit}>Cancel</Button>
            <Button type="submit" variant="contained">
              Update
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {prompts.length === 0 ? (
        <Alert severity="info">No prompts found. Create your first prompt!</Alert>
      ) : (
        <Grid container spacing={3}>
          {prompts.map((prompt) => (
            // @ts-expect-error - prompt type has missing properties
            <Grid item xs={12} sm={6} md={4} key={prompt.id} sx={{ display: 'flex' }}>
              <Card onClick={() => navigate(`/prompts/${prompt.id}`)} sx={{ cursor: 'pointer', '&:hover': { boxShadow: 3 } }}>
                <CardContent>
                  <Typography variant="h5" component="div">
                    {prompt.title}
                  </Typography>
                  <Typography sx={{ mb: 1.5 }} color="text.secondary">
                    Created: {formatDateTime(prompt.created_at)}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    {prompt.content}
                  </Typography>
                  {prompt.tags && prompt.tags.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      {prompt.tags.map((tag: string) => (
                        <Chip key={tag} label={tag} size="small" sx={{ mr: 1, mb: 1 }} />
                      ))}
                    </Box>
                  )}
                </CardContent>
                <CardActions>
                  <IconButton onClick={(e) => { e.stopPropagation(); handleEdit(prompt); }} aria-label="edit">
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={(e) => { e.stopPropagation(); handleDelete(prompt.id); }} aria-label="delete">
                    <DeleteIcon />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </div>
  );
}