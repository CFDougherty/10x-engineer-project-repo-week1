import { useState, useEffect, useRef } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Alert,
  CircularProgress,
  Fab,
} from '@mui/material';
import { KeyboardArrowUp as KeyboardArrowUpIcon } from '@mui/icons-material';
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

const CARD_ROW_HEIGHT = 334; // 310px card + 24px gap

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

  // ── Responsive column count ───────────────────────────────────────────────
  const containerRef = useRef<HTMLDivElement>(null);
  const [cols, setCols] = useState(2);
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(([entry]) => {
      setCols(entry.contentRect.width > 600 ? 2 : 1);
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, [open]);

  // ── Scroll tracking inside DialogContent ─────────────────────────────────
  // Callback ref: fires the moment the DOM node mounts (regardless of MUI Dialog's
  // portal/animation timing), storing in state triggers a re-render + the effect.
  const [contentEl, setContentEl] = useState<HTMLDivElement | null>(null);
  const [contentScroll, setContentScroll] = useState(0);
  useEffect(() => {
    if (!contentEl || !open) return;
    setContentScroll(0);
    const handle = () => setContentScroll(contentEl.scrollTop);
    contentEl.addEventListener('scroll', handle, { passive: true });
    return () => contentEl.removeEventListener('scroll', handle);
  }, [contentEl, open]);

  const collectionName = collections.find(c => c.id === collectionId)?.name;
  const collectionPrompts = collectionId
    ? prompts.filter((p: Prompt) => p.collection_id === collectionId)
    : [];

  // ── Position indicator ────────────────────────────────────────────────────
  const currentRow = contentEl
    ? Math.ceil((contentScroll + contentEl.clientHeight) / CARD_ROW_HEIGHT)
    : 0;
  const currentIndex = Math.min(currentRow * cols, collectionPrompts.length);
  const showScrollTop = contentScroll > 200;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Prompts in {collectionName ?? 'Collection'}
      </DialogTitle>
      <DialogContent sx={{ p: 0 }}>
        <Box ref={setContentEl} sx={{ overflowY: 'auto', maxHeight: '70vh', px: 3, pt: 1, pb: 2 }}>
          {loading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : collectionPrompts.length === 0 ? (
            <Alert severity="info">No prompts in this collection.</Alert>
          ) : (
            <div ref={containerRef}>
              <Box display="grid" gridTemplateColumns={`repeat(${cols}, 1fr)`} gap={3}>
                {collectionPrompts.map((prompt) => (
                  <PromptCard
                    key={prompt.id}
                    prompt={prompt}
                    collectionName={collectionName}
                    onEdit={onPromptEdit}
                    onDelete={onPromptDelete}
                    onViewHistory={onPromptViewHistory}
                  />
                ))}
              </Box>
            </div>
          )}
        </Box>
      </DialogContent>
      <DialogActions sx={{ justifyContent: 'space-between', alignItems: 'center', px: 3, py: 1.5 }}>
        {/* Position indicator */}
        {collectionPrompts.length > 0 ? (
          <Box
            sx={{
              typography: 'caption',
              color: 'text.secondary',
              bgcolor: 'background.paper',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 2,
              px: 1.5,
              py: 0.5,
              boxShadow: 1,
              userSelect: 'none',
            }}
          >
            {currentIndex} / {collectionPrompts.length}
          </Box>
        ) : (
          <Box />
        )}

        {/* Scroll-to-top + Close */}
        <Box display="flex" alignItems="center" gap={1}>
          {showScrollTop && (
            <Fab
              size="small"
              aria-label="Scroll to top"
              onClick={() => contentEl?.scrollTo({ top: 0, behavior: 'smooth' })}
            >
              <KeyboardArrowUpIcon />
            </Fab>
          )}
          <Button onClick={onClose}>Close</Button>
        </Box>
      </DialogActions>
    </Dialog>
  );
}
