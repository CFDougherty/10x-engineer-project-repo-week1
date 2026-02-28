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
  Button,
  Divider
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
  collectionName?: string;
  onEdit: (promptId: string) => void;
  onDelete: (promptId: string) => void;
  onViewHistory: (promptId: string) => void;
}

export default function PromptCard({ prompt, collectionName, onEdit, onDelete, onViewHistory }: PromptCardProps) {
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
            <Box sx={{ mb: 2 }}>
              <Divider sx={{ mb: 1 }}>Description</Divider>
              <Typography variant="body2" sx={{ wordBreak: 'break-word', mt: 1 }}>
                {prompt.description}
              </Typography>
            </Box>
          )}
          <Box sx={{ mb: 2 }}>
            <Divider sx={{ mb: 1 }}>Content</Divider>
            <Typography variant="body1" sx={{ wordBreak: 'break-word', whiteSpace: 'pre-wrap', mt: 1 }}>
              {prompt.content}
            </Typography>
          </Box>
          {prompt.tags && prompt.tags.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Divider sx={{ mb: 1 }}>Tags</Divider>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                {prompt.tags.map((tag: string) => (
                  <Chip key={tag} label={tag} size="small" />
                ))}
              </Box>
            </Box>
          )}
          {collectionName && (
            <Box sx={{ mb: 2 }}>
              <Divider sx={{ mb: 1 }}>Collection</Divider>
              <Typography variant="body2" sx={{ mt: 1 }}>
                {collectionName}
              </Typography>
            </Box>
          )}
          <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mt: 1 }}>
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
