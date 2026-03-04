import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCollections } from '../contexts/CollectionsContext';
import { usePrompts } from '../contexts/PromptsContext';
import {
  Button,
  Typography,
  CircularProgress,
  Alert,
  Box,
  Fab,
} from '@mui/material';
import { Grid } from '@mui/material';
import { Add as AddIcon, KeyboardArrowUp as KeyboardArrowUpIcon } from '@mui/icons-material';
import ConfirmationDialog from '../components/ConfirmationDialog';
import VersionHistoryDialog from '../components/VersionHistoryDialog';
import CollectionCard from '../components/CollectionCard';
import CollectionCreationDialog from '../components/CollectionCreationDialog';
import CollectionPromptsDialog from '../components/CollectionPromptsDialog';
import type { Collection } from '../types/collection';
import type { Prompt } from '../types/prompt';

export default function CollectionsPage() {
  const navigate = useNavigate();
  const { collections, loading, error, remove, refetch } = useCollections();
  const { prompts: allPrompts, refetch: refetchPrompts, remove: removePrompt } = usePrompts();

  // ── Scroll tracking ───────────────────────────────────────────────────────
  const [scrollY, setScrollY] = useState(0);
  useEffect(() => {
    const handle = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handle, { passive: true });
    return () => window.removeEventListener('scroll', handle);
  }, []);
  const showScrollTop = scrollY > 400;
  const docScrollable = document.documentElement.scrollHeight - window.innerHeight;
  const fraction = docScrollable > 0 ? scrollY / docScrollable : 1;
  const currentIndex = Math.min(Math.round(fraction * collections.length), collections.length);

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
            <Grid key={collection.id} size={{ xs: 12, sm: 6, md: 4, lg: 3 }} sx={{ display: 'flex' }}>
              <CollectionCard
                collection={collection}
                promptCount={allPrompts.filter((p: Prompt) => p.collection_id === collection.id).length}
                onEdit={handleCollectionEdit}
                onDelete={handleCollectionDeleteRequest}
                onViewPrompts={handleViewPrompts}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Position indicator */}
      {collections.length > 0 && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 24,
            left: 24,
            zIndex: 1200,
            bgcolor: 'background.paper',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2,
            px: 1.5,
            py: 0.5,
            typography: 'caption',
            color: 'text.secondary',
            boxShadow: 1,
            userSelect: 'none',
          }}
        >
          {currentIndex} / {collections.length}
        </Box>
      )}

      {/* Scroll-to-top */}
      {showScrollTop && (
        <Fab
          size="small"
          aria-label="Scroll to top"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          sx={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1200 }}
        >
          <KeyboardArrowUpIcon />
        </Fab>
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
