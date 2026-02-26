import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  MenuItem,
  CircularProgress
} from '@mui/material';
import { useCollections } from '../hooks/useCollections';
import { usePrompts } from '../hooks/usePrompts';

interface PromptCreationDialogProps {
  open: boolean;
  onClose: () => void;
  initialCollectionId?: string;
  onPromptCreated?: () => void;
  refetchCollections?: () => void;
}

export default function PromptCreationDialog({
  open,
  onClose,
  initialCollectionId,
  onPromptCreated,
  refetchCollections,
}: PromptCreationDialogProps) {
  const { create: createPrompt } = usePrompts();
  const { collections, create: createCollection } = useCollections();
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    tags: '',
    collectionId: initialCollectionId || '',
  });
  const [isCreatingCollection, setIsCreatingCollection] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [showCollectionDialog, setShowCollectionDialog] = useState(false);

  const handleClose = () => {
    setFormData({
      title: '',
      content: '',
      tags: '',
      collectionId: initialCollectionId || '',
    });
    setNewCollectionName('');
    setIsCreatingCollection(false);
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
        tags: tagsArray,
        collection_id: formData.collectionId || undefined,
      };

      await createPrompt(promptData);
      if (onPromptCreated) {
        onPromptCreated();
      }
      // Refetch collections to update prompt_ids
      if (refetchCollections) {
        refetchCollections();
      }
      handleClose();
    } catch (err) {
      console.error('Error saving prompt:', err);
    }
  };

  const handleCreateNewCollection = async () => {
    if (!newCollectionName.trim()) return;

    setIsCreatingCollection(true);
    try {
      const collectionData = {
        name: newCollectionName.trim(),
        description: '',
      };
      const newCollection = await createCollection(collectionData);
      setFormData({
        ...formData,
        collectionId: newCollection.id,
      });
      setShowCollectionDialog(false);
    } catch (err) {
      console.error('Error creating collection:', err);
    } finally {
      setIsCreatingCollection(false);
    }
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
      <Dialog open={showCollectionDialog} onClose={() => setShowCollectionDialog(false)}>
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
            <Button onClick={() => setShowCollectionDialog(false)}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={isCreatingCollection || !newCollectionName.trim()}
            >
              {isCreatingCollection ? <CircularProgress size={24} /> : 'Create'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </>
  );
}