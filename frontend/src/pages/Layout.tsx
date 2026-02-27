import { Outlet } from 'react-router-dom';
import { Container, useMediaQuery } from '@mui/material';
import type { Theme } from '@mui/material';
import { useState } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'));

  return (
    <div>
      <Header
        onMenuClick={() => setSidebarOpen(true)}
        isMobile={isMobile}
      />
      <Container sx={{ mt: 4 }}>
        <Outlet />
      </Container>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
    </div>
  );
}