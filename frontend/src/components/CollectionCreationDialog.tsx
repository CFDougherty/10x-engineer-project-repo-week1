import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  CircularProgress
} from '@mui/material';
import { useCollections } from '../contexts/CollectionsContext';

interface CollectionCreationDialogProps {
  open: boolean;
  onClose: () => void;
  onCollectionCreated?: (collectionId: string) => void;
}

export default function CollectionCreationDialog({
  open,
  onClose,
  onCollectionCreated,
}: CollectionCreationDialogProps) {
  const { create: createCollection, refetch } = useCollections();
  const [newCollectionName, setNewCollectionName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleClose = () => {
    setNewCollectionName('');
    setIsCreating(false);
    onClose();
  };

  const handleCreateNewCollection = async () => {
    if (!newCollectionName.trim()) return;

    setIsCreating(true);
    try {
      const collectionData = {
        name: newCollectionName.trim(),
        description: '',
      };
      const newCollection = await createCollection(collectionData);
      // Refresh collections to ensure all components get the updated list
      await refetch();
      if (onCollectionCreated) {
        onCollectionCreated(newCollection.id);
      }
      handleClose();
    } catch (err) {
      console.error('Error creating collection:', err);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose}>
      <form onSubmit={(e) => {
        e.preventDefault();
        handleCreateNewCollection();
      }}>
        <DialogTitle>Create New Collection</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Collection Name"
            fullWidth
            value={newCollectionName}
            onChange={(e) => setNewCollectionName(e.target.value)}
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={isCreating || !newCollectionName.trim()}
          >
            {isCreating ? <CircularProgress size={24} /> : 'Create'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}