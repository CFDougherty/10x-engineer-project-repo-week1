import { useState } from 'react';
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
  Button
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon, History as HistoryIcon } from '@mui/icons-material';
import { formatDateTime } from '../utils/dateUtils';

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
  onEdit: (promptId: string) => void;
  onDelete: (promptId: string) => void;
  onViewHistory: (promptId: string) => void;
}

export default function PromptCard({ prompt, onEdit, onDelete, onViewHistory }: PromptCardProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Card sx={{ cursor: 'pointer', transition: 'box-shadow 0.3s', width: 350, overflow: 'hidden' }}>
        <CardContent onClick={() => setOpen(true)}>
          <Box display="flex" justifyContent="space-between" alignItems="start">
            <Typography variant="h5" component="div" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
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

          <Typography sx={{ mb: 1.5 }} color="text.secondary">
            Created: {formatDateTime(prompt.created_at)}
          </Typography>

          <Typography variant="body2" sx={{ mb: 2, wordBreak: 'break-word', whiteSpace: 'normal', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>
            {prompt.content.substring(0, 100)}...
          </Typography>

          {prompt.tags && prompt.tags.length > 0 && (
            <Box sx={{ mb: 2, overflow: 'hidden' }}>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {prompt.tags.map((tag: string) => (
                  <Chip key={tag} label={tag} size="small" sx={{ mr: 1, mb: 1 }} />
                ))}
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{prompt.title}</DialogTitle>
        <DialogContent dividers>
          {prompt.description && (
            <Typography variant="body2" paragraph sx={{ mb: 2, wordBreak: 'break-word' }}>
              <strong>Description:</strong> {prompt.description}
            </Typography>
          )}
          <Typography variant="body1" paragraph sx={{ mb: 2, wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}>
            {prompt.content}
          </Typography>
          {prompt.tags && prompt.tags.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {prompt.tags.map((tag: string) => (
                <Chip key={tag} label={tag} size="small" />
              ))}
            </Box>
          )}
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="caption" color="text.secondary">
              Created: {formatDateTime(prompt.created_at)}
            </Typography>
            {prompt.updated_at && prompt.updated_at !== prompt.created_at && (
              <Typography variant="caption" color="text.secondary">
                Updated: {formatDateTime(prompt.updated_at)}
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
