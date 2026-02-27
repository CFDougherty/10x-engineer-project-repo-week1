import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPromptById, updatePrompt, deletePrompt } from '../services/apiClient';
import type { Prompt } from '../types/prompt';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  CircularProgress,
  Alert,
  TextField,
  MenuItem,
} from '@mui/material';
import { Delete as DeleteIcon, ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import ConfirmationDialog from './ConfirmationDialog';
import { useCollections } from '../hooks/useCollections';

export default function PromptDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState<Prompt | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({
    title: '',
    content: '',
    tags: '',
    collectionId: '',
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const { collections } = useCollections();

  useEffect(() => {
    if (!id) return;

    const fetchPrompt = async () => {
      try {
        setLoading(true);
        const response = await getPromptById(id);
        setPrompt(response.data);
        setEditData({
          title: response.data.title,
          content: response.data.content,
          tags: response.data.tags?.join(', ') || '',
          collectionId: response.data.collection_id || '',
        });
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch prompt');
        console.error('Error fetching prompt:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPrompt();
  }, [id]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !prompt) return;

    try {
      const tagsArray = editData.tags.split(',').map((tag: string) => tag.trim()).filter(Boolean);
      const promptData = {
        title: editData.title,
        content: editData.content,
        tags: tagsArray,
        collection_id: editData.collectionId || undefined,
      };

      const response = await updatePrompt(id, promptData);
      setPrompt(response.data);
      setEditMode(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update prompt');
      console.error('Error updating prompt:', err);
    }
  };

  const handleDelete = async () => {
    if (!id) return;

    try {
      await deletePrompt(id);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete prompt');
      console.error('Error deleting prompt:', err);
    }
  };

  if (loading && !prompt) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!prompt) {
    return <Alert severity="error">Prompt not found</Alert>;
  }

  return (
    <div>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
          variant="outlined"
        >
          Back to Prompts
        </Button>
        <Box>
          <Button
            startIcon={<DeleteIcon />}
            color="error"
            variant="outlined"
            onClick={() => setDeleteDialogOpen(true)}
          >
            Delete
          </Button>
        </Box>
      </Box>

      {!editMode ? (
        <Card>
          <CardContent>
            <Typography variant="h3" component="h1" gutterBottom>
              {prompt.title}
            </Typography>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography color="text.secondary">
                Created: {new Date(prompt.created_at).toLocaleDateString()}
              </Typography>
              {prompt.updated_at && prompt.updated_at !== prompt.created_at && (
                <Typography color="text.secondary">
                  Updated: {new Date(prompt.updated_at).toLocaleDateString()}
                </Typography>
              )}
            </Box>
            {prompt.collection_id && (
              <Box sx={{ mb: 2 }}>
                <Typography color="text.secondary" variant="body2">
                  Collection: {collections.find(c => c.id === prompt.collection_id)?.name || 'Unknown'}
                </Typography>
              </Box>
            )}
            {prompt.tags && prompt.tags.length > 0 && (
              <Box sx={{ mb: 3 }}>
                {prompt.tags.map((tag) => (
                  <Chip key={tag} label={tag} size="small" sx={{ mr: 1, mb: 1 }} />
                ))}
              </Box>
            )}
            <Typography variant="body1" paragraph>
              {prompt.content}
            </Typography>
          </CardContent>
          <CardActions>
            <Button size="small" onClick={() => setEditMode(true)}>
              Edit
            </Button>
          </CardActions>
        </Card>
      ) : (
        <Card>
          <form id="edit-prompt-form" onSubmit={handleUpdate}>
            <CardContent>
              <TextField
                fullWidth
                margin="normal"
                label="Title"
                value={editData.title}
                onChange={(e) => setEditData({...editData, title: e.target.value})}
                required
              />
              <TextField
                fullWidth
                margin="normal"
                label="Content"
                multiline
                rows={8}
                value={editData.content}
                onChange={(e) => setEditData({...editData, content: e.target.value})}
                required
              />
              <TextField
                fullWidth
                margin="normal"
                label="Tags (comma separated)"
                value={editData.tags}
                onChange={(e) => setEditData({...editData, tags: e.target.value})}
              />
              <TextField
                select
                fullWidth
                margin="normal"
                label="Collection"
                value={editData.collectionId}
                onChange={(e) => setEditData({...editData, collectionId: e.target.value})}
              >
                <MenuItem value="">None (no collection)</MenuItem>
                {collections.map((collection) => (
                  <MenuItem key={collection.id} value={collection.id}>
                    {collection.name}
                  </MenuItem>
                ))}
              </TextField>
            </CardContent>
            <CardActions>
              <Button type="button" onClick={() => setEditMode(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="contained">
                Save Changes
              </Button>
            </CardActions>
          </form>
        </Card>
      )}

      <ConfirmationDialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDelete}
        title="Delete Prompt"
        message="Are you sure you want to delete this prompt? This action cannot be undone."
        confirmText="Delete"
      />
    </div>
  );
}