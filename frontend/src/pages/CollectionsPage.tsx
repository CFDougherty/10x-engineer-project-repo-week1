import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCollections } from '../contexts/CollectionsContext';
import { usePrompts } from '../contexts/PromptsContext';
import {
  Button,
  Typography,
  CircularProgress,
  Alert,
  Box
} from '@mui/material';
import { Grid } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import ConfirmationDialog from '../components/ConfirmationDialog';
import VersionHistoryDialog from '../components/VersionHistoryDialog';
import CollectionCard from '../components/CollectionCard';
import CollectionCreationDialog from '../components/CollectionCreationDialog';
import CollectionPromptsDialog from '../components/CollectionPromptsDialog';
import type { Collection } from '../types/collection';

export default function CollectionsPage() {
  const navigate = useNavigate();
  const { collections, loading, error, remove, refetch } = useCollections();
  const { prompts: allPrompts, refetch: refetchPrompts, remove: removePrompt } = usePrompts();

  // Create dialog
  const [createOpen, setCreateOpen] = useState(false);

  // Edit dialog
  const [editingCollection, setEditingCollection] = useState<Collection | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  // Collection delete confirmation
  const [collectionToDelete, setCollectionToDelete] = useState<string | null>(null);
  const [collectionDeleteDialogOpen, setCollectionDeleteDialogOpen] = useState(false);

  // View prompts dialog
  const [viewPromptsCollectionId, setViewPromptsCollectionId] = useState<string | null>(null);
  const [viewPromptsDialogOpen, setViewPromptsDialogOpen] = useState(false);

  // Prompt actions
  const [promptToDelete, setPromptToDelete] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [historyPromptId, setHistoryPromptId] = useState<string | null>(null);

  const handleCollectionEdit = (id: string) => {
    const collection = collections.find(c => c.id === id) ?? null;
    setEditingCollection(collection);
    setEditDialogOpen(true);
  };

  const handleCollectionDeleteRequest = (id: string) => {
    setCollectionToDelete(id);
    setCollectionDeleteDialogOpen(true);
  };

  const confirmDeleteCollection = async () => {
    if (!collectionToDelete) return;
    try {
      await remove(collectionToDelete);
      await refetchPrompts();
      setCollectionDeleteDialogOpen(false);
      setCollectionToDelete(null);
    } catch (err) {
      console.error('Error deleting collection:', err);
    }
  };

  const handleViewPrompts = (id: string) => {
    setViewPromptsCollectionId(id);
    setViewPromptsDialogOpen(true);
  };

  const handlePromptEdit = (promptId: string) => {
    navigate(`/prompts/${promptId}`);
  };

  const handlePromptDelete = (promptId: string) => {
    setPromptToDelete(promptId);
    setDeleteDialogOpen(true);
  };

  const confirmDeletePrompt = async () => {
    if (!promptToDelete) return;
    try {
      await removePrompt(promptToDelete);
      setDeleteDialogOpen(false);
      setPromptToDelete(null);
    } catch (err) {
      console.error('Error deleting prompt:', err);
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
          onClick={() => setCreateOpen(true)}
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
            <Grid key={collection.id} item xs={12} sm={6} md={4} sx={{ display: 'flex' }}>
              <CollectionCard
                collection={collection}
                promptCount={allPrompts.filter(p => p.collection_id === collection.id).length}
                onEdit={handleCollectionEdit}
                onDelete={handleCollectionDeleteRequest}
                onViewPrompts={handleViewPrompts}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Collection */}
      <CollectionCreationDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />

      {/* Edit Collection */}
      <CollectionCreationDialog
        open={editDialogOpen}
        onClose={() => { setEditDialogOpen(false); setEditingCollection(null); }}
        mode="edit"
        initialData={editingCollection ? { name: editingCollection.name, description: editingCollection.description } : undefined}
        collectionId={editingCollection?.id}
        onCollectionUpdated={() => { refetch(); setEditDialogOpen(false); setEditingCollection(null); }}
      />

      {/* View Prompts */}
      <CollectionPromptsDialog
        open={viewPromptsDialogOpen}
        onClose={() => { setViewPromptsDialogOpen(false); setViewPromptsCollectionId(null); }}
        collectionId={viewPromptsCollectionId}
        onPromptEdit={handlePromptEdit}
        onPromptDelete={handlePromptDelete}
        onPromptViewHistory={(id) => setHistoryPromptId(id)}
      />

      {/* Delete Collection Confirmation */}
      <ConfirmationDialog
        open={collectionDeleteDialogOpen}
        onClose={() => setCollectionDeleteDialogOpen(false)}
        onConfirm={confirmDeleteCollection}
        title="Delete Collection"
        message="Are you sure you want to delete this collection? This action cannot be undone."
        confirmText="Delete"
      />

      {/* Delete Prompt Confirmation */}
      <ConfirmationDialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={confirmDeletePrompt}
        title="Delete Prompt"
        message="Are you sure you want to delete this prompt? This action cannot be undone."
        confirmText="Delete"
      />

      {/* Version History */}
      <VersionHistoryDialog
        open={historyPromptId !== null}
        onClose={() => setHistoryPromptId(null)}
        promptId={historyPromptId ?? ''}
        onRestored={refetchPrompts}
      />
    </div>
  );
}
