import { Outlet } from 'react-router-dom';
import { Box, useMediaQuery } from '@mui/material';
import type { Theme } from '@mui/material';
import { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import AdminToolsDialog from '../components/AdminToolsDialog';
import EmbeddingStatusBar from '../components/EmbeddingStatusBar';
import PopulateStatusBar from '../components/PopulateStatusBar';
import { useQueryClient } from '@tanstack/react-query';
import { connectSSE, disconnectSSE } from '../services/sseClient';
import { useCollections } from '../contexts/CollectionsContext';
import { PROMPTS_QUERY_KEY } from '../contexts/PromptsContext';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [adminDialogOpen, setAdminDialogOpen] = useState(false);
  const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'));
  const queryClient = useQueryClient();
  const { refetch: refetchCollections } = useCollections();

  useEffect(() => {
    const handleDataChange = () => {
      // Invalidate all prompt queries (any filter combination).
      // TanStack Query refetches active queries immediately; inactive ones on next mount.
      queryClient.invalidateQueries({ queryKey: PROMPTS_QUERY_KEY });
      refetchCollections();
    };

    connectSSE(handleDataChange);
    return () => disconnectSSE();
  }, [queryClient, refetchCollections]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header
        onMenuClick={() => setSidebarOpen(true)}
        isMobile={isMobile}
        onAdminClick={() => setAdminDialogOpen(true)}
      />
      <EmbeddingStatusBar />
      <PopulateStatusBar />
      <Box component="main" sx={{ px: { xs: 2, md: 3 }, pt: 4, flexGrow: 1, maxWidth: { xs: '100%', md: '67%' }, mx: 'auto', width: '100%', boxSizing: 'border-box' }}>
        <Outlet />
      </Box>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <AdminToolsDialog open={adminDialogOpen} onClose={() => setAdminDialogOpen(false)} />
    </div>
  );
}
