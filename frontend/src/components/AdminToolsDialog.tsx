import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, Typography, Box, TextField, Switch,
  FormControlLabel, Slider, Divider,
} from '@mui/material';
import {
  populateTestData, clearAllData, clearTestData,
} from '../services/apiClient';
import type { PopulateConfig } from '../services/apiClient';
import ConfirmationDialog from './ConfirmationDialog';
import { usePrompts } from '../contexts/PromptsContext';
import { useCollections } from '../contexts/CollectionsContext';

interface AdminToolsDialogProps {
  open: boolean;
  onClose: () => void;
}

const MAX_PROMPTS = 10_000;
const MAX_COLLECTIONS = 1_000;
const MAX_TAGS = 500;

const AdminToolsDialog: React.FC<AdminToolsDialogProps> = ({ open, onClose }) => {
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [actionType, setActionType] = useState<'populate' | 'clear' | 'clearTest' | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generation config
  const [numPrompts, setNumPrompts] = useState(40);
  const [numCollections, setNumCollections] = useState(4);
  const [collectionChance, setCollectionChance] = useState(60);
  const [tagsPerPrompt, setTagsPerPrompt] = useState(3);
  const [randomSeed, setRandomSeed] = useState('');
  const [tagAsTestFill, setTagAsTestFill] = useState(false);
  const [appendMode, setAppendMode] = useState(false);

  const { refetch: refetchPrompts } = usePrompts();
  const { refetch: refetchCollections } = useCollections();

  const handlePopulateTestData = () => {
    setActionType('populate');
    setConfirmationOpen(true);
  };

  const handleClearTestData = () => {
    setActionType('clearTest');
    setConfirmationOpen(true);
  };

  const handleClearAllData = () => {
    setActionType('clear');
    setConfirmationOpen(true);
  };

  const executeAction = async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (actionType === 'populate') {
        const config: PopulateConfig = {
          num_prompts: numPrompts,
          num_collections: numCollections,
          collection_chance: collectionChance / 100,
          tags_per_prompt: tagsPerPrompt,
          random_seed: randomSeed !== '' ? parseInt(randomSeed, 10) : null,
          tag_as_test_fill: tagAsTestFill,
          append_mode: appendMode,
        };
        await populateTestData(config); // returns immediately (202); PopulateStatusBar tracks progress
        onClose();
      } else if (actionType === 'clearTest') {
        await clearTestData();
        await refetchPrompts();
        await refetchCollections();
        onClose();
      } else if (actionType === 'clear') {
        await clearAllData();
        await refetchPrompts();
        await refetchCollections();
        onClose();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
      setConfirmationOpen(false);
    }
  };

  const handleCancel = () => {
    setConfirmationOpen(false);
    setActionType(null);
  };

  const confirmationMessage = () => {
    if (actionType === 'populate') {
      return appendMode
        ? `Add ${numPrompts.toLocaleString()} prompts to the existing data?`
        : `Replace all existing data with ${numPrompts.toLocaleString()} new prompts?`;
    }
    if (actionType === 'clearTest') return "Delete all prompts tagged 'test fill'?";
    return 'Delete all data? This action cannot be undone.';
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>Admin Tools</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>

            {/* ── Generate Test Data ── */}
            <Typography variant="subtitle2" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 1 }}>
              Generate Test Data
            </Typography>

            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField
                label="Prompts"
                type="number"
                size="small"
                value={numPrompts}
                onChange={e => setNumPrompts(Math.min(MAX_PROMPTS, Math.max(1, parseInt(e.target.value) || 1)))}
                disabled={isLoading}
              />
              <TextField
                label="Collections"
                type="number"
                size="small"
                value={numCollections}
                onChange={e => setNumCollections(Math.min(MAX_COLLECTIONS, Math.max(0, parseInt(e.target.value) || 0)))}
                disabled={isLoading}
              />
              <TextField
                label="Tags per prompt"
                type="number"
                size="small"
                value={tagsPerPrompt}
                onChange={e => setTagsPerPrompt(Math.min(MAX_TAGS, Math.max(0, parseInt(e.target.value) || 0)))}
                disabled={isLoading}
              />
              <TextField
                label="Random seed (optional)"
                type="number"
                size="small"
                value={randomSeed}
                onChange={e => setRandomSeed(e.target.value)}
                placeholder="leave blank for random"
                disabled={isLoading}
              />
            </Box>

            <Box>
              <Typography variant="body2" gutterBottom>
                Collection assignment chance: {collectionChance}%
              </Typography>
              <Slider
                value={collectionChance}
                onChange={(_, v) => setCollectionChance(v as number)}
                min={0}
                max={100}
                disabled={isLoading}
                size="small"
              />
            </Box>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={tagAsTestFill}
                    onChange={e => setTagAsTestFill(e.target.checked)}
                    disabled={isLoading}
                    size="small"
                  />
                }
                label={<Typography variant="body2">Tag all generated data as "test fill"</Typography>}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={appendMode}
                    onChange={e => setAppendMode(e.target.checked)}
                    disabled={isLoading}
                    size="small"
                  />
                }
                label={<Typography variant="body2">Append to existing data (don't flush first)</Typography>}
              />
            </Box>

            <Button
              variant="contained"
              color="primary"
              onClick={handlePopulateTestData}
              disabled={isLoading}
            >
              Populate Test Data
            </Button>

            <Divider />

            {/* ── Manage Data ── */}
            <Typography variant="subtitle2" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 1 }}>
              Manage Data
            </Typography>

            <Button
              variant="outlined"
              color="warning"
              onClick={handleClearTestData}
              disabled={isLoading}
            >
              Clear Test Data ("test fill" tagged)
            </Button>

            <Button
              variant="outlined"
              color="error"
              onClick={handleClearAllData}
              disabled={isLoading}
            >
              Clear All Data
            </Button>

            {error && (
              <Typography color="error" variant="body2">
                {error}
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={isLoading}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmationDialog
        open={confirmationOpen}
        onClose={handleCancel}
        onConfirm={executeAction}
        title="Confirm Action"
        message={confirmationMessage()}
        loading={isLoading}
        error={error}
      />
    </>
  );
};

export default AdminToolsDialog;
