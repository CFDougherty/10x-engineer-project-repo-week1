import { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Divider,
  Chip
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { formatDateTime } from '../utils/dateUtils';

interface CollectionCardProps {
  collection: {
    id: string;
    name: string;
    description?: string;
    created_at: string;
    updated_at: string;
    prompt_ids?: string[];
  };
  promptCount: number;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onViewPrompts: (id: string) => void;
}

export default function CollectionCard({ collection, promptCount, onEdit, onDelete, onViewPrompts }: CollectionCardProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Card sx={{ cursor: 'pointer', transition: 'box-shadow 0.3s', width: '100%', minHeight: '20rem', display: 'flex', flexDirection: 'column' }}>
        <CardContent onClick={() => setOpen(true)} sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
          <Box display="flex" justifyContent="space-between" alignItems="start">
            <Typography variant="h5" component="div" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {collection.name}
            </Typography>
            <Box display="flex" gap={1}>
              <IconButton size="small" onClick={(e) => { e.stopPropagation(); onEdit(collection.id); }}>
                <EditIcon fontSize="small" />
              </IconButton>
              <IconButton size="small" onClick={(e) => { e.stopPropagation(); onDelete(collection.id); }}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>

          <Typography sx={{ mb: 1.5 }} color="text.secondary">
            Created: {formatDateTime(collection.created_at)}
          </Typography>

          {collection.description && (
            <Typography variant="body2" sx={{ mb: 1.5, wordBreak: 'break-word', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
              {collection.description}
            </Typography>
          )}

          <Box sx={{ mt: 'auto', pt: 1 }}>
            <Chip label={`${promptCount} ${promptCount === 1 ? 'prompt' : 'prompts'}`} size="small" />
          </Box>
        </CardContent>
      </Card>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{collection.name}</DialogTitle>
        <DialogContent dividers>
          {collection.description && (
            <Box sx={{ mb: 2 }}>
              <Divider sx={{ mb: 1 }}>Description</Divider>
              <Typography variant="body2" sx={{ wordBreak: 'break-word', mt: 1 }}>
                {collection.description}
              </Typography>
            </Box>
          )}
          <Box sx={{ mb: 2 }}>
            <Divider sx={{ mb: 1 }}>Details</Divider>
            <Typography variant="body2" sx={{ mt: 1 }}>
              {promptCount} {promptCount === 1 ? 'prompt' : 'prompts'}
            </Typography>
          </Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Created: {formatDateTime(collection.created_at)}
            </Typography>
            {collection.updated_at && collection.updated_at !== collection.created_at && (
              <Typography variant="caption" color="text.secondary">
                Updated: {formatDateTime(collection.updated_at)}
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Box sx={{ flex: 1, display: 'flex', gap: 1 }}>
            <IconButton size="small" onClick={() => { setOpen(false); onEdit(collection.id); }}>
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => { setOpen(false); onDelete(collection.id); }}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
          <Button onClick={() => { setOpen(false); onViewPrompts(collection.id); }}>
            View Prompts
          </Button>
          <Button onClick={() => setOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
