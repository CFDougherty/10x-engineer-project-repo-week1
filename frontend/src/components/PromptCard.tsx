import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Divider,
  CircularProgress,
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon, History as HistoryIcon } from '@mui/icons-material';
import { formatDateTime } from '../utils/dateUtils';
import { getPromptById } from '../services/apiClient';

interface PromptCardProps {
  prompt: {
    id: string;
    title: string;
    content: string;
    description?: string;
    tags?: string[];
    created_at: string;
    updated_at: string;
  };
  collectionName?: string;
  cols?: number;
  onEdit: (promptId: string) => void;
  onDelete: (promptId: string) => void;
  onViewHistory: (promptId: string) => void;
}

export default function PromptCard({ prompt, collectionName, cols = 1, onEdit, onDelete, onViewHistory }: PromptCardProps) {
  const [open, setOpen] = useState(false);

  // Fetch the full prompt only when the detail dialog is open.
  // The list endpoint returns truncated content (≤300 chars); the detail
  // endpoint always returns the full text.  TanStack Query caches the result
  // so repeated opens are instant.
  const { data: fullPrompt, isLoading: loadingFull } = useQuery({
    queryKey: ['prompt', prompt.id],
    queryFn: () => getPromptById(prompt.id).then((r) => r.data),
    enabled: open,
    staleTime: 30_000,
  });

  const dialogPrompt = fullPrompt ?? prompt;

  return (
    <>
      <Card sx={{ cursor: 'pointer', transition: 'box-shadow 0.3s', width: '100%', overflow: 'hidden', minHeight: '20rem' }}>
        <CardContent onClick={() => setOpen(true)}>
          <Box display="flex" justifyContent="space-between" alignItems="start">
            <Typography variant="h6" component="div" sx={{ overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
              {prompt.title}
            </Typography>
            <Box display="flex" gap={1}>
              <IconButton size="small" onClick={(e) => { e.stopPropagation(); onEdit(prompt.id); }}>
                <EditIcon fontSize="small" />
              </IconButton>
              <IconButton size="small" onClick={(e) => { e.stopPropagation(); onViewHistory(prompt.id); }}>
                <HistoryIcon fontSize="small" />
              </IconButton>
              <IconButton size="small" onClick={(e) => { e.stopPropagation(); onDelete(prompt.id); }}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>

          <Typography variant="caption" sx={{ mb: 1 }} color="text.secondary" display="block">
            Created: {formatDateTime(prompt.created_at)}
          </Typography>

          <Typography variant="body2" sx={{ mb: 2, wordBreak: 'break-word', whiteSpace: 'normal', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: cols === 4 ? 4 : cols === 3 ? 5 : cols === 2 ? 6 : 8, WebkitBoxOrient: 'vertical' }}>
            {prompt.content}
          </Typography>

          {prompt.tags && prompt.tags.length > 0 && (() => {
            const MAX_VISIBLE = 3;
            const visible = prompt.tags.slice(0, MAX_VISIBLE);
            const overflow = prompt.tags.length - MAX_VISIBLE;
            return (
              <Box sx={{ mb: 2, overflow: 'hidden' }}>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {visible.map((tag: string) => (
                    <Chip key={tag} label={tag} size="small" sx={{ mr: 1, mb: 1 }} />
                  ))}
                  {overflow > 0 && (
                    <Chip label={`+${overflow}`} size="small" variant="outlined" sx={{ mr: 1, mb: 1 }} />
                  )}
                </Box>
              </Box>
            );
          })()}
        </CardContent>
      </Card>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{dialogPrompt.title}</DialogTitle>
        <DialogContent dividers>
          {loadingFull ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress size={32} />
            </Box>
          ) : (
            <>
              {dialogPrompt.description && (
                <Box sx={{ mb: 2 }}>
                  <Divider sx={{ mb: 1 }}>Description</Divider>
                  <Typography variant="body2" sx={{ wordBreak: 'break-word', mt: 1 }}>
                    {dialogPrompt.description}
                  </Typography>
                </Box>
              )}
              <Box sx={{ mb: 2 }}>
                <Divider sx={{ mb: 1 }}>Content</Divider>
                <Typography variant="body1" sx={{ wordBreak: 'break-word', whiteSpace: 'pre-wrap', mt: 1 }}>
                  {dialogPrompt.content}
                </Typography>
              </Box>
              {dialogPrompt.tags && dialogPrompt.tags.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Divider sx={{ mb: 1 }}>Tags</Divider>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                    {dialogPrompt.tags.map((tag: string) => (
                      <Chip key={tag} label={tag} size="small" />
                    ))}
                  </Box>
                </Box>
              )}
              {collectionName && (
                <Box sx={{ mb: 2 }}>
                  <Divider sx={{ mb: 1 }}>Collection</Divider>
                  <Typography variant="body2" sx={{ mt: 1 }}>{collectionName}</Typography>
                </Box>
              )}
              <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Created: {formatDateTime(dialogPrompt.created_at)}
                </Typography>
                {dialogPrompt.updated_at && dialogPrompt.updated_at !== dialogPrompt.created_at && (
                  <Typography variant="caption" color="text.secondary">
                    Updated: {formatDateTime(dialogPrompt.updated_at)}
                  </Typography>
                )}
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Box sx={{ flex: 1, display: 'flex', gap: 1 }}>
            <IconButton size="small" onClick={() => { setOpen(false); onEdit(prompt.id); }}>
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => { setOpen(false); onViewHistory(prompt.id); }}>
              <HistoryIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => { setOpen(false); onDelete(prompt.id); }}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
          <Button onClick={() => setOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
