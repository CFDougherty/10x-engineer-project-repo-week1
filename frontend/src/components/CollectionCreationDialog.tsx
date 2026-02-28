import { useState, useEffect } from 'react';
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
  mode?: 'create' | 'edit';
  initialData?: { name: string; description?: string };
  collectionId?: string;
  onCollectionUpdated?: () => void;
}

export default function CollectionCreationDialog({
  open,
  onClose,
  onCollectionCreated,
  mode = 'create',
  initialData,
  collectionId,
  onCollectionUpdated,
}: CollectionCreationDialogProps) {
  const { create: createCollection, update: updateCollection, refetch } = useCollections();
  const [newCollectionName, setNewCollectionName] = useState('');
  const [newCollectionDescription, setNewCollectionDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setNewCollectionName(initialData?.name ?? '');
      setNewCollectionDescription(initialData?.description ?? '');
    }
  }, [open, initialData]);

  const handleClose = () => {
    setNewCollectionName('');
    setNewCollectionDescription('');
    setIsSubmitting(false);
    onClose();
  };

  const handleSubmit = async () => {
    if (!newCollectionName.trim()) return;

    setIsSubmitting(true);
    try {
      if (mode === 'edit' && collectionId) {
        await updateCollection(collectionId, {
          name: newCollectionName.trim(),
          description: newCollectionDescription.trim(),
        });
        onCollectionUpdated?.();
        handleClose();
      } else {
        const collectionData = {
          name: newCollectionName.trim(),
          description: newCollectionDescription.trim(),
        };
        const newCollection = await createCollection(collectionData);
        await refetch();
        onCollectionCreated?.(newCollection.id);
        handleClose();
      }
    } catch (err) {
      console.error('Error saving collection:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isEdit = mode === 'edit';

  return (
    <Dialog open={open} onClose={handleClose}>
      <form onSubmit={(e) => {
        e.preventDefault();
        handleSubmit();
      }}>
        <DialogTitle>{isEdit ? 'Edit Collection' : 'Create New Collection'}</DialogTitle>
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
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={4}
            value={newCollectionDescription}
            onChange={(e) => setNewCollectionDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={isSubmitting || !newCollectionName.trim()}
          >
            {isSubmitting ? <CircularProgress size={24} /> : isEdit ? 'Save' : 'Create'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
