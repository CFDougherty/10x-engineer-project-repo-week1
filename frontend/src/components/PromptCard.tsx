import { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Collapse,
  Divider
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
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
}

export default function PromptCard({ prompt, onEdit, onDelete }: PromptCardProps) {
  const [expanded, setExpanded] = useState(false);

  const handleClick = () => {
    setExpanded(!expanded);
  };

  return (
    <Card sx={{ cursor: 'pointer', transition: 'box-shadow 0.3s' }}>
      <CardContent onClick={handleClick}>
        <Box display="flex" justifyContent="space-between" alignItems="start">
          <Typography variant="h5" component="div">
            {prompt.title}
          </Typography>
          <Box display="flex" gap={1}>
            <IconButton size="small" onClick={(e) => { e.stopPropagation(); onEdit(prompt.id); }}>
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={(e) => { e.stopPropagation(); onDelete(prompt.id); }}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        <Typography sx={{ mb: 1.5 }} color="text.secondary">
          Created: {formatDateTime(prompt.created_at)}
        </Typography>

        <Typography variant="body2" sx={{ mb: 2 }}>
          {prompt.content.substring(0, 100)}...
        </Typography>

        {prompt.tags && prompt.tags.length > 0 && (
          <Box sx={{ mb: 2 }}>
            {prompt.tags.map((tag: string) => (
              <Chip key={tag} label={tag} size="small" sx={{ mr: 1, mb: 1 }} />
            ))}
          </Box>
        )}
      </CardContent>

      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <Divider />
        <Box sx={{ p: 2 }}>
          {prompt.description && (
            <Typography variant="body2" paragraph sx={{ mb: 2 }}>
              <strong>Description:</strong> {prompt.description}
            </Typography>
          )}
          <Typography variant="body1" paragraph sx={{ mb: 2 }}>
            {prompt.content}
          </Typography>

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
        </Box>
      </Collapse>
    </Card>
  );
}