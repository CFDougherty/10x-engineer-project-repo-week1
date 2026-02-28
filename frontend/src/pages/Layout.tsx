import { Outlet } from 'react-router-dom';
import { Container, useMediaQuery } from '@mui/material';
import type { Theme } from '@mui/material';
import { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import AdminToolsDialog from '../components/AdminToolsDialog';
import { connectSSE, disconnectSSE } from '../services/sseClient';
import { usePrompts } from '../contexts/PromptsContext';
import { useCollections } from '../contexts/CollectionsContext';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [adminDialogOpen, setAdminDialogOpen] = useState(false);
  const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'));
  const { refetch: refetchPrompts } = usePrompts();
  const { refetch: refetchCollections } = useCollections();

  // Connect to SSE when component mounts, disconnect when unmounts
  useEffect(() => {
    const handleDataChange = async () => {
      console.log('Received data change notification, refetching...');
      await refetchPrompts();
      await refetchCollections();
    };

    connectSSE(handleDataChange);

    return () => {
      disconnectSSE();
    };
  }, [refetchPrompts, refetchCollections]);

  const handleAdminClick = () => {
    setAdminDialogOpen(true);
  };

  const handleAdminClose = () => {
    setAdminDialogOpen(false);
  };

  return (
    <div>
      <Header
        onMenuClick={() => setSidebarOpen(true)}
        isMobile={isMobile}
        onAdminClick={handleAdminClick}
      />
      <Container sx={{ mt: 4 }}>
        <Outlet />
      </Container>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <AdminToolsDialog open={adminDialogOpen} onClose={handleAdminClose} />
    </div>
  );
}
