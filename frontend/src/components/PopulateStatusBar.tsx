import { useEffect, useState, useRef, useCallback } from 'react';
import { Box, LinearProgress, Typography, Chip, IconButton } from '@mui/material';
import { CheckCircle as CheckCircleIcon, DataObject as DataObjectIcon, Close as CloseIcon, Error as ErrorIcon } from '@mui/icons-material';
import { getPopulateStatus } from '../services/apiClient';
import type { PopulateProgress } from '../services/apiClient';

const FAST_POLL_MS = 500;   // while a populate is running
const IDLE_POLL_MS = 5000;  // when nothing is happening
const AUTO_HIDE_DELAY_MS = 5000;

export default function PopulateStatusBar() {
  const [status, setStatus] = useState<PopulateProgress | null>(null);
  const [visible, setVisible] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await getPopulateStatus();
      setStatus(res.data);
    } catch {
      // Silently ignore — backend may not be ready yet
    }
  }, []);

  // Two-speed polling: fast when active, slow when idle
  useEffect(() => {
    fetchStatus();
    const ms = status?.active ? FAST_POLL_MS : IDLE_POLL_MS;
    intervalRef.current = setInterval(fetchStatus, ms);
    return stopPolling;
  }, [status?.active, fetchStatus, stopPolling]);

  // Auto-hide after clean completion (not on error — keep visible until dismissed)
  useEffect(() => {
    if (status && !status.active && status.current > 0 && !status.error && !hideTimerRef.current) {
      hideTimerRef.current = setTimeout(() => setVisible(false), AUTO_HIDE_DELAY_MS);
    }
  }, [status]);

  // Reset visibility when a new populate starts
  useEffect(() => {
    if (status?.active) {
      setVisible(true);
      if (hideTimerRef.current) {
        clearTimeout(hideTimerRef.current);
        hideTimerRef.current = null;
      }
    }
  }, [status?.active]);

  // Cleanup hide timer on unmount
  useEffect(() => {
    return () => {
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    };
  }, []);

  const handleDismiss = () => {
    stopPolling();
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    setVisible(false);
  };

  // Hidden when: no status yet, nothing has run and no error, or user dismissed
  if (!status || (!status.active && status.current === 0 && !status.error) || !visible) return null;

  const pct = status.total > 0 ? Math.round((status.current / status.total) * 100) : 0;

  const phaseLabels: Record<string, string> = {
    generating: 'Generating prompts…',
    inserting: 'Inserting into database…',
    versioning: 'Creating versions…',
    collections: 'Creating collections…',
    assigning: 'Assigning to collections…',
    done: 'Finalizing…',
  };
  const phaseLabel = (status.phase && phaseLabels[status.phase]) ?? 'Generating prompts…';

  if (!status.active && status.error) {
    return (
      <Box
        sx={{
          bgcolor: 'error.dark',
          px: 2,
          py: 0.5,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 1,
        }}
      >
        <ErrorIcon sx={{ fontSize: 14, color: 'error.contrastText' }} />
        <Typography variant="caption" sx={{ color: 'error.contrastText', fontWeight: 500 }}>
          Generation failed: {status.error}
        </Typography>
        <IconButton size="small" onClick={handleDismiss} sx={{ color: 'error.contrastText', p: 0.25, ml: 0.5 }}>
          <CloseIcon sx={{ fontSize: 14 }} />
        </IconButton>
      </Box>
    );
  }

  if (!status.active && status.current > 0) {
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
          {status.current.toLocaleString()} prompts created successfully
        </Typography>
        <IconButton size="small" onClick={handleDismiss} sx={{ color: 'success.contrastText', p: 0.25, ml: 0.5 }}>
          <CloseIcon sx={{ fontSize: 14 }} />
        </IconButton>
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
        <DataObjectIcon sx={{ fontSize: 14, color: 'text.secondary', flexShrink: 0 }} />
        <Typography variant="caption" sx={{ color: 'text.secondary', flexShrink: 0 }}>
          {phaseLabel}
        </Typography>
        <Box sx={{ flexGrow: 1 }}>
          <LinearProgress
            variant="determinate"
            value={pct}
            sx={{ borderRadius: 1, height: 6 }}
          />
        </Box>
        <Chip
          label={`${status.current.toLocaleString()} / ${status.total.toLocaleString()}`}
          size="small"
          sx={{ height: 18, fontSize: 11, flexShrink: 0 }}
        />
        <IconButton size="small" onClick={handleDismiss} sx={{ p: 0.25 }}>
          <CloseIcon sx={{ fontSize: 14 }} />
        </IconButton>
      </Box>
    </Box>
  );
}
