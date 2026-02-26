import { useState } from 'react';
import { usePrompts } from '../hooks/usePrompts';
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
  IconButton
} from '@mui/material';
import Grid from '@mui/material/Grid';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';

export default function PromptsPage() {
  const { prompts, loading, error, create, update, remove } = usePrompts();
  const [open, setOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<any>(null);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    tags: '',
  });

  const handleOpen = () => {
    setEditingPrompt(null);
    setFormData({ title: '', content: '', tags: '' });
    setOpen(true);
  };

  const handleEdit = (prompt: any) => {
    setEditingPrompt(prompt);
    setFormData({
      title: prompt.title,
      content: prompt.content,
      tags: prompt.tags?.join(', ') || '',
    });
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const tagsArray = formData.tags.split(',').map((tag: string) => tag.trim()).filter(Boolean);
      const promptData = {
        title: formData.title,
        content: formData.content,
        tags: tagsArray,
      };

      if (editingPrompt) {
        await update(editingPrompt.id, promptData);
      } else {
        await create(promptData);
      }
      handleClose();
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

      {prompts.length === 0 ? (
        <Alert severity="info">No prompts found. Create your first prompt!</Alert>
      ) : (
        <Grid container spacing={3}>
          {prompts.map((prompt) => (
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

      {/* Create/Edit Dialog */}
      <Dialog open={open} onClose={handleClose}>
        <form onSubmit={handleSubmit}>
          <DialogTitle>{editingPrompt ? 'Edit Prompt' : 'Create New Prompt'}</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Title"
              fullWidth
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              required
            />
            <TextField
              margin="dense"
              label="Content"
              fullWidth
              multiline
              rows={4}
              value={formData.content}
              onChange={(e) => setFormData({...formData, content: e.target.value})}
              required
            />
            <TextField
              margin="dense"
              label="Tags (comma separated)"
              fullWidth
              value={formData.tags}
              onChange={(e) => setFormData({...formData, tags: e.target.value})}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button type="submit" variant="contained">
              {editingPrompt ? 'Update' : 'Create'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </div>
  );
}