import { useEffect, useState, useRef } from 'react';
import { Box, LinearProgress, Typography, Chip } from '@mui/material';
import { CheckCircle as CheckCircleIcon, Memory as MemoryIcon } from '@mui/icons-material';
import { getEmbeddingStatus } from '../services/apiClient';

interface EmbeddingStatus {
  total: number;
  embedded: number;
  complete: boolean;
}

const POLL_INTERVAL_MS = 4000;

export default function EmbeddingStatusBar() {
  const [status, setStatus] = useState<EmbeddingStatus | null>(null);
  const [visible, setVisible] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await getEmbeddingStatus();
      const next = res.data;
      setStatus(next);

      if (next.complete) {
        // Stop polling once all are embedded
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        // Fade out the "complete" message after 6 seconds if there are no prompts
        // that need embedding (i.e. total === 0 is also "complete")
        if (next.total > 0) {
          hideTimerRef.current = setTimeout(() => setVisible(false), 6000);
        }
      }
    } catch {
      // Silently ignore — backend may not be ready yet
    }
  };

  useEffect(() => {
    fetchStatus();
    intervalRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    };
  }, []);

  // Nothing to show when: no data yet, total is 0 (no prompts), or bar was hidden
  if (!status || status.total === 0 || !visible) return null;

  const pct = Math.round((status.embedded / status.total) * 100);

  if (status.complete) {
    return (
      <Box
        sx={{
          bgcolor: 'success.dark',
          px: 2,
          py: 0.5,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 1,
        }}
      >
        <CheckCircleIcon sx={{ fontSize: 14, color: 'success.contrastText' }} />
        <Typography variant="caption" sx={{ color: 'success.contrastText', fontWeight: 500 }}>
          All {status.total} prompts indexed for semantic search
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
      <Box
        sx={{
          px: 2,
          py: 0.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
        }}
      >
        <MemoryIcon sx={{ fontSize: 14, color: 'text.secondary', flexShrink: 0 }} />
        <Typography variant="caption" sx={{ color: 'text.secondary', flexShrink: 0 }}>
          Indexing embeddings
        </Typography>
        <Box sx={{ flexGrow: 1 }}>
          <LinearProgress
            variant="determinate"
            value={pct}
            sx={{ borderRadius: 1, height: 6 }}
          />
        </Box>
        <Chip
          label={`${status.embedded} / ${status.total}`}
          size="small"
          sx={{ height: 18, fontSize: 11, flexShrink: 0 }}
        />
      </Box>
    </Box>
  );
}
