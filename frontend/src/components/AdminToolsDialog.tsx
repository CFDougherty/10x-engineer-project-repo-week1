import React, { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Box } from '@mui/material';
import { populateTestData, clearAllData } from '../services/apiClient';
import ConfirmationDialog from './ConfirmationDialog';
import { usePrompts } from '../hooks/usePrompts';
import { useCollections } from '../contexts/CollectionsContext';

interface AdminToolsDialogProps {
  open: boolean;
  onClose: () => void;
}

const AdminToolsDialog: React.FC<AdminToolsDialogProps> = ({ open, onClose }) => {
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [actionType, setActionType] = useState<'populate' | 'clear' | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get refetch functions from context
  const { refetch: refetchPrompts } = usePrompts();
  const { refetch: refetchCollections } = useCollections();

  const handlePopulateTestData = async () => {
    setActionType('populate');
    setConfirmationOpen(true);
  };

  const handleClearAllData = async () => {
    setActionType('clear');
    setConfirmationOpen(true);
  };

  const executeAction = async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (actionType === 'populate') {
        await populateTestData();
        // Refresh data after population
        await refetchPrompts();
        await refetchCollections();
      } else if (actionType === 'clear') {
        await clearAllData();
        // Refresh data after clearing
        await refetchPrompts();
        await refetchCollections();
      }
      onClose();
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

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>Admin Tools</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body1" sx={{ mb: 3 }}>
              Manage test data and application state.
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                variant="contained"
                color="primary"
                onClick={handlePopulateTestData}
                disabled={isLoading}
              >
                Populate Test Data
              </Button>

              <Button
                variant="outlined"
                color="error"
                onClick={handleClearAllData}
                disabled={isLoading}
              >
                Clear All Data
              </Button>
            </Box>

            {error && (
              <Typography color="error" sx={{ mt: 2 }}>
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
        message={
          actionType === 'populate'
            ? 'Are you sure you want to populate test data? This will replace any existing data.'
            : 'Are you sure you want to clear all data? This action cannot be undone.'
        }
        loading={isLoading}
        error={error}
      />
    </>
  );
};

export default AdminToolsDialog;