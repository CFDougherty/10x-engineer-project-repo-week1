import { useState } from 'react';
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
import { usePrompts } from '../hooks/usePrompts';
import CollectionCreationDialog from './CollectionCreationDialog';

interface PromptCreationDialogProps {
  open: boolean;
  onClose: () => void;
  initialCollectionId?: string;
  onPromptCreated?: () => void;
}

export default function PromptCreationDialog({
  open,
  onClose,
  initialCollectionId,
  onPromptCreated,
}: PromptCreationDialogProps) {
  const { create: createPrompt } = usePrompts();
  const { collections } = useCollections();
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    description: '',
    tags: '',
    collectionId: initialCollectionId || '',
  });
  const [showCollectionDialog, setShowCollectionDialog] = useState(false);

  const handleClose = () => {
    setFormData({
      title: '',
      content: '',
      description: '',
      tags: '',
      collectionId: initialCollectionId || '',
    });
    setShowCollectionDialog(false);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
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

      await createPrompt(promptData);
      if (onPromptCreated) {
        onPromptCreated();
      }
      handleClose();
    } catch (err) {
      console.error('Error saving prompt:', err);
    }
  };

  const handleCollectionCreated = () => {
    // After collection is created, it will be automatically available in the collections list
    // due to the refetch in CollectionCreationDialog
  };

  return (
    <>
      {/* Create/Edit Prompt Dialog */}
      <Dialog open={open} onClose={handleClose}>
        <form onSubmit={handleSubmit}>
          <DialogTitle>Create New Prompt</DialogTitle>
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
              Create
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