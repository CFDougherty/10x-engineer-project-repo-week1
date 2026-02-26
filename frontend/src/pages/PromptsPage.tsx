import { useState } from 'react';
import { usePrompts } from '../hooks/usePrompts';
import { useCollections } from '../hooks/useCollections';
import {
  Button,
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
  MenuItem
} from '@mui/material';
import { Grid } from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import PromptCreationDialog from '../components/PromptCreationDialog';

export default function PromptsPage() {
  const { prompts, loading, error, update, remove } = usePrompts();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<any>(null);
  const [editFormData, setEditFormData] = useState({
    title: '',
    content: '',
    tags: '',
    collectionId: '',
  });
  const { collections, refetch } = useCollections();

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
      // Refetch collections to update prompt_ids if collection changed
      await refetch();
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
        <Typography variant="h4">Prompts</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleOpen}
        >
          New Prompt
        </Button>
      </Box>

      {/* Prompt Creation Dialog */}
      <PromptCreationDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        refetchCollections={refetch}
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
              <Card>
                <CardContent>
                  <Typography variant="h5" component="div">
                    {prompt.title}
                  </Typography>
                  <Typography sx={{ mb: 1.5 }} color="text.secondary">
                    Created: {new Date(prompt.created_at).toLocaleDateString()}
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
                  <IconButton onClick={() => handleEdit(prompt)} aria-label="edit">
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDelete(prompt.id)} aria-label="delete">
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