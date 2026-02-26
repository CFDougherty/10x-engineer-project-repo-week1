import { Outlet } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Container, IconButton, useMediaQuery } from '@mui/material';
import { Link } from 'react-router-dom';
import type { Theme } from '@mui/material';
import { Menu as MenuIcon } from '@mui/icons-material';
import { useState } from 'react';
import Sidebar from '../components/Sidebar';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'));

  return (
    <div>
      <AppBar position="static">
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setSidebarOpen(true)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            <Link to="/" style={{ color: 'white', textDecoration: 'none' }}>
              PromptLab
            </Link>
          </Typography>
          {!isMobile && (
            <>
              <Button color="inherit" component={Link} to="/">
                Prompts
              </Button>
              <Button color="inherit" component={Link} to="/collections">
                Collections
              </Button>
            </>
          )}
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }}>
        <Outlet />
      </Container>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
    </div>
  );
}
