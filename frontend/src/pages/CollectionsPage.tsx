import { useState } from 'react';
import { useCollections } from '../hooks/useCollections';
import { usePrompts } from '../hooks/usePrompts';
import {
  Button,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  IconButton,
  Chip
} from '@mui/material';
import { Grid } from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';

export default function CollectionsPage() {
  const { collections, loading, error, create, remove } = useCollections();
  const { prompts: allPrompts } = usePrompts();
  const [open, setOpen] = useState(false);
  const [viewingCollectionId, setViewingCollectionId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });

  // Get prompts for the currently viewed collection
  const collectionPrompts = viewingCollectionId
    ? allPrompts.filter(prompt => prompt.collection_id === viewingCollectionId)
    : [];

  const handleOpen = () => {
    setFormData({ name: '', description: '' });
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const collectionData = {
        name: formData.name,
        description: formData.description,
      };
      await create(collectionData);
      handleClose();
    } catch (err) {
      console.error('Error creating collection:', err);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await remove(id);
    } catch (err) {
      console.error('Error deleting collection:', err);
    }
  };

  if (loading && collections.length === 0) {
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
        <Typography variant="h4">Collections</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleOpen}
        >
          New Collection
        </Button>
      </Box>

      {collections.length === 0 ? (
        <Alert severity="info">No collections found. Create your first collection!</Alert>
      ) : (
        <Grid container spacing={3}>
          {collections.map((collection) => (
            // @ts-expect-error - collection type has missing properties
            <Grid key={collection.id} item xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h5" component="div">
                    {collection.name}
                  </Typography>
                  {collection.description && (
                    <Typography sx={{ mb: 1.5 }} color="text.secondary">
                      {collection.description}
                    </Typography>
                  )}
                  <Typography sx={{ mb: 1.5 }} color="text.secondary">
                    Created: {new Date(collection.created_at).toLocaleDateString()}
                  </Typography>
                  <Typography variant="body2">
                    {allPrompts.filter(prompt => prompt.collection_id === collection.id).length} prompts
                  </Typography>
                </CardContent>
                <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setViewingCollectionId(collection.id)}
                  >
                    View Prompts
                  </Button>
                  <IconButton onClick={() => handleDelete(collection.id)} aria-label="delete">
                    <DeleteIcon />
                  </IconButton>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* View Prompts in Collection */}
      {viewingCollectionId && (
        <Box mt={4}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h5">
              Prompts in {collections.find(c => c.id === viewingCollectionId)?.name}
            </Typography>
            <Button
              variant="outlined"
              onClick={() => setViewingCollectionId(null)}
            >
              Back to Collections
            </Button>
          </Box>

          {collectionPrompts.length === 0 ? (
            <Alert severity="info">No prompts in this collection. Create one!</Alert>
          ) : (
            <Grid container spacing={3}>
              {collectionPrompts.map((prompt) => (
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
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      )}


      {/* Create Collection Dialog */}
      <Dialog open={open} onClose={handleClose}>
        <form onSubmit={handleSubmit}>
          <DialogTitle>Create New Collection</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Name"
              fullWidth
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
            <TextField
              margin="dense"
              label="Description"
              fullWidth
              multiline
              rows={4}
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button type="submit" variant="contained">
              Create
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </div>
  );
}