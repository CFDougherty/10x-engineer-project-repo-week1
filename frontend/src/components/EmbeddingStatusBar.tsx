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
const IDLE_POLL_MS = 15000;  // slow-poll while complete, to detect new embedding jobs

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
        // Switch to slow polling while idle — keeps the component alive to detect new jobs
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = setInterval(fetchStatus, IDLE_POLL_MS);
        if (next.total > 0) {
          hideTimerRef.current = setTimeout(() => setVisible(false), 6000);
        }
      } else if (next.total > 0) {
        // New embedding work detected — re-show bar and restore fast polling
        setVisible(true);
        if (hideTimerRef.current) {
          clearTimeout(hideTimerRef.current);
          hideTimerRef.current = null;
        }
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS);
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
