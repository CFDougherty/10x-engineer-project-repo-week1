import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  CircularProgress,
  Box,
  Alert,
  Tooltip,
  TextField,
  Chip
} from '@mui/material';
import { formatDateTime } from '../utils/dateUtils';
import type { VersionList, VersionSummary, PromptVersion } from '../types/prompt';
import { getPromptVersions, getPromptVersion, promotePromptVersion, updatePrompt } from '../services/apiClient';
import { Restore as RestoreIcon } from '@mui/icons-material';
import ConfirmationDialog from './ConfirmationDialog';

interface VersionHistoryDialogProps {
  open: boolean;
  onClose: () => void;
  promptId: string;
  onRestored?: () => void;
}

export default function VersionHistoryDialog({ open, onClose, promptId, onRestored }: VersionHistoryDialogProps) {
  const [versions, setVersions] = useState<VersionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<PromptVersion | null>(null);
  const [versionDetailsOpen, setVersionDetailsOpen] = useState(false);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [restoreLoading, setRestoreLoading] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const [editedTitle, setEditedTitle] = useState('');
  const [editedContent, setEditedContent] = useState('');
  const [editedDescription, setEditedDescription] = useState('');

  useEffect(() => {
    if (open && promptId) {
      fetchVersions();
    }
  }, [open, promptId]);

  const fetchVersions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getPromptVersions(promptId);
      const data: VersionList = response.data;
      setVersions(data.versions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch version history');
      console.error('Error fetching versions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVersionClick = async (version: VersionSummary) => {
    try {
      const response = await getPromptVersion(promptId, version.version);
      const v: PromptVersion = response.data;
      setSelectedVersion(v);
      setEditedTitle(v.title);
      setEditedContent(v.content);
      setEditedDescription(v.description ?? '');
      setVersionDetailsOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch version details');
      console.error('Error fetching version details:', err);
    }
  };

  const hasEdits = selectedVersion
    ? editedTitle !== selectedVersion.title ||
      editedContent !== selectedVersion.content ||
      editedDescription !== (selectedVersion.description ?? '')
    : false;

  const handleRestore = async () => {
    if (!selectedVersion) return;

    try {
      setRestoreLoading(true);
      setRestoreError(null);
      if (hasEdits) {
        await updatePrompt(promptId, {
          title: editedTitle,
          content: editedContent,
          description: editedDescription || undefined,
          tags: selectedVersion.tags,
          collection_id: selectedVersion.collection_id,
        });
      } else {
        await promotePromptVersion(promptId, selectedVersion.version);
      }
      onRestored?.();
      await fetchVersions();
      setRestoreDialogOpen(false);
      setVersionDetailsOpen(false);
      setError(null);
    } catch (err) {
      setRestoreError(err instanceof Error ? err.message : 'Failed to restore version');
      console.error('Error restoring version:', err);
    } finally {
      setRestoreLoading(false);
    }
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle>Version History</DialogTitle>
        <DialogContent>
          {loading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : error ? (
            <Alert severity="error">{error}</Alert>
          ) : versions.length === 0 ? (
            <Alert severity="info">No version history available</Alert>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Version</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Description</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {versions.map((version) => (
                    <TableRow key={version.version} hover onClick={() => handleVersionClick(version)} style={{ cursor: 'pointer' }}>
                      <TableCell>{version.version}</TableCell>
                      <TableCell>{formatDateTime(version.created_at)}</TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap title={version.title}>
                          {version.title}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={version.description || 'No description'}>
                          <Typography variant="body2" color="text.secondary" noWrap>
                            {version.description || '-'}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Close</Button>
          {versions.length > 0 && (
            <Button onClick={fetchVersions} disabled={loading}>
              {loading ? <CircularProgress size={20} /> : 'Refresh'}
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Version Details Dialog */}
      <Dialog open={versionDetailsOpen} onClose={() => setVersionDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Version {selectedVersion?.version} Details</DialogTitle>
        <DialogContent>
          {selectedVersion && (
            <>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                Edit the fields below to restore with modifications. Previous versions remain immutable.
              </Typography>
              <TextField
                fullWidth
                margin="normal"
                label="Title"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
              />
              <TextField
                fullWidth
                margin="normal"
                label="Content"
                multiline
                rows={8}
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
              />
              <TextField
                fullWidth
                margin="normal"
                label="Description"
                value={editedDescription}
                onChange={(e) => setEditedDescription(e.target.value)}
              />
              {selectedVersion.tags && selectedVersion.tags.length > 0 && (
                <Box sx={{ mb: 2, mt: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Tags:
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {selectedVersion.tags.map((tag) => (
                      <Chip key={tag} label={tag} size="small" />
                    ))}
                  </Box>
                </Box>
              )}
              {selectedVersion.collection_id && (
                <TextField
                  fullWidth
                  margin="normal"
                  label="Collection ID"
                  value={selectedVersion.collection_id}
                  InputProps={{ readOnly: true }}
                />
              )}
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                Created: {formatDateTime(selectedVersion.created_at)}
              </Typography>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVersionDetailsOpen(false)}>Close</Button>
          <Button
            startIcon={<RestoreIcon />}
            color="primary"
            variant="contained"
            onClick={() => setRestoreDialogOpen(true)}
          >
            {hasEdits ? 'Restore with Edits' : 'Restore This Version'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Restore Confirmation Dialog */}
      <ConfirmationDialog
        open={restoreDialogOpen}
        onClose={() => setRestoreDialogOpen(false)}
        onConfirm={handleRestore}
        title="Restore Version"
        message={hasEdits
          ? `Are you sure you want to restore version ${selectedVersion?.version} with your edits? This will create a new version with your modifications.`
          : `Are you sure you want to restore version ${selectedVersion?.version}? This will create a new version based on this old version.`
        }
        confirmText="Restore"
        loading={restoreLoading}
        error={restoreError}
      />
    </>
  );
}