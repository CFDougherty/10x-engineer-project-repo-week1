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
  Alert
} from '@mui/material';
import { formatDateTime } from '../utils/dateUtils';
import type { VersionList, VersionSummary } from '../types/prompt';
import { getPromptVersions } from '../services/apiClient';

interface VersionHistoryDialogProps {
  open: boolean;
  onClose: () => void;
  promptId: string;
}

export default function VersionHistoryDialog({ open, onClose, promptId }: VersionHistoryDialogProps) {
  const [versions, setVersions] = useState<VersionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return (
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
                  <TableRow key={version.version} hover>
                    <TableCell>{version.version}</TableCell>
                    <TableCell>{formatDateTime(version.created_at)}</TableCell>
                    <TableCell>
                      <Typography variant="body2">{version.title}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {version.description || '-'}
                      </Typography>
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
  );
}