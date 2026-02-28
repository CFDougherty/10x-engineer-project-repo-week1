import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  MenuItem
} from '@mui/material';
import { useCollections } from '../contexts/CollectionsContext';
import CollectionCreationDialog from './CollectionCreationDialog';

interface PromptFormDialogProps {
  open: boolean;
  onClose: () => void;
  mode: 'create' | 'edit';
  initialData?: {
    title: string;
    content: string;
    description?: string;
    tags?: string[];
    collection_id?: string;
  };
  onSubmit: (promptData: {
    title: string;
    content: string;
    description?: string;
    tags: string[];
    collection_id?: string;
  }) => Promise<void>;
  initialCollectionId?: string;
  onPromptCreated?: () => void;
}

export default function PromptFormDialog({
  open,
  onClose,
  mode,
  initialData,
  onSubmit,
  initialCollectionId,
  onPromptCreated,
}: PromptFormDialogProps) {
  const { collections } = useCollections();
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    description: '',
    tags: '',
    collectionId: initialCollectionId || '',
  });
  const [showCollectionDialog, setShowCollectionDialog] = useState(false);

  // Reset form when dialog opens or mode/initialData changes
  useEffect(() => {
    if (open) {
      if (mode === 'edit' && initialData) {
        setFormData({
          title: initialData.title || '',
          content: initialData.content || '',
          description: initialData.description || '',
          tags: initialData.tags?.join(', ') || '',
          collectionId: initialData.collection_id || '',
        });
      } else {
        setFormData({
          title: '',
          content: '',
          description: '',
          tags: '',
          collectionId: initialCollectionId || '',
        });
      }
      setShowCollectionDialog(false);
    }
  }, [open, mode, initialData, initialCollectionId]);

  const handleClose = () => {
    onClose();
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const tagsArray = formData.tags.split(',').map((tag: string) => tag.trim()).filter(Boolean);
      const promptData = {
        title: formData.title,
        content: formData.content,
        description: formData.description || undefined,
        tags: tagsArray,
        collection_id: formData.collectionId || undefined,
      };

      await onSubmit(promptData);
      if (onPromptCreated) {
        onPromptCreated();
      }
      handleClose();
    } catch (err) {
      console.error('Error saving prompt:', err);
    }
  };

  const handleCollectionCreated = (collectionId: string) => {
    // After collection is created, set it as the selected collection in the dropdown
    setFormData({...formData, collectionId});
  };

  return (
    <>
      {/* Create/Edit Prompt Dialog */}
      <Dialog open={open} onClose={handleClose}>
        <form onSubmit={handleFormSubmit}>
          <DialogTitle>{mode === 'create' ? 'Create New Prompt' : 'Edit Prompt'}</DialogTitle>
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
              label="Description"
              fullWidth
              multiline
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
            />
            <TextField
              margin="dense"
              label="Tags (comma separated)"
              fullWidth
              value={formData.tags}
              onChange={(e) => setFormData({...formData, tags: e.target.value})}
            />
            <TextField
              select
              margin="dense"
              label="Collection"
              fullWidth
              value={formData.collectionId}
              onChange={(e) => setFormData({...formData, collectionId: e.target.value})}
            >
              <MenuItem value="">None (no collection)</MenuItem>
              {collections.map((collection) => (
                <MenuItem key={collection.id} value={collection.id}>
                  {collection.name}
                </MenuItem>
              ))}
              <MenuItem value="__create_new__" onClick={(e) => {
                e.stopPropagation();
                setShowCollectionDialog(true);
              }}>
                + Create new collection...
              </MenuItem>
            </TextField>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button type="submit" variant="contained">
              {mode === 'create' ? 'Create' : 'Update'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Create New Collection Dialog */}
      <CollectionCreationDialog
        open={showCollectionDialog}
        onClose={() => setShowCollectionDialog(false)}
        onCollectionCreated={handleCollectionCreated}
      />
    </>
  );
}