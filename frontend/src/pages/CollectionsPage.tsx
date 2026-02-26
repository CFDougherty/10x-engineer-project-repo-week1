import { useState, useEffect } from 'react';
import { getCollections, createCollection, deleteCollection } from '../services/apiClient';
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
  IconButton
} from '@mui/material';
import Grid from '@mui/material/Grid';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';

export default function CollectionsPage() {
  const [collections, setCollections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });

  const fetchCollections = async () => {
    try {
      setLoading(true);
      const response = await getCollections();
      setCollections(response.data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch collections');
      console.error('Error fetching collections:', err);
    } finally {
      setLoading(false);
    }
  };

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
      await createCollection(collectionData);
      await fetchCollections();
      handleClose();
    } catch (err) {
      console.error('Error creating collection:', err);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteCollection(id);
      await fetchCollections();
    } catch (err) {
      console.error('Error deleting collection:', err);
    }
  };

  useEffect(() => {
    fetchCollections();
  }, []);

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
            <Grid item xs={12} sm={6} md={4} key={collection.id}>
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
                    {collection.prompt_ids?.length || 0} prompts
                  </Typography>
                </CardContent>
                <Box sx={{ p: 2 }}>
                  <IconButton onClick={() => handleDelete(collection.id)} aria-label="delete">
                    <DeleteIcon />
                  </IconButton>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
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