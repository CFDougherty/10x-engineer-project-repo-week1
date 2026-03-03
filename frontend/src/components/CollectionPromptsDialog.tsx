import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';
import { Grid } from '@mui/material';
import { usePrompts } from '../contexts/PromptsContext';
import { useCollections } from '../contexts/CollectionsContext';
import type { Prompt } from '../types/prompt';
import PromptCard from './PromptCard';

interface CollectionPromptsDialogProps {
  open: boolean;
  onClose: () => void;
  collectionId: string | null;
  onPromptEdit: (id: string) => void;
  onPromptDelete: (id: string) => void;
  onPromptViewHistory: (id: string) => void;
}

export default function CollectionPromptsDialog({
  open,
  onClose,
  collectionId,
  onPromptEdit,
  onPromptDelete,
  onPromptViewHistory,
}: CollectionPromptsDialogProps) {
  const { prompts, loading } = usePrompts();
  const { collections } = useCollections();

  const collectionName = collections.find(c => c.id === collectionId)?.name;
  const collectionPrompts = collectionId
    ? prompts.filter((p: Prompt) => p.collection_id === collectionId)
    : [];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Prompts in {collectionName ?? 'Collection'}
      </DialogTitle>
      <DialogContent sx={{ overflowY: 'auto', maxHeight: '70vh' }}>
        {loading ? (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        ) : collectionPrompts.length === 0 ? (
          <Alert severity="info">No prompts in this collection.</Alert>
        ) : (
          <Grid container spacing={3}>
            {collectionPrompts.map((prompt) => (
              // @ts-expect-error - prompt type has missing properties
              <Grid item xs={12} sm={6} key={prompt.id}>
                <PromptCard
                  prompt={prompt}
                  collectionName={collectionName}
                  onEdit={onPromptEdit}
                  onDelete={onPromptDelete}
                  onViewHistory={onPromptViewHistory}
                />
              </Grid>
            ))}
          </Grid>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
