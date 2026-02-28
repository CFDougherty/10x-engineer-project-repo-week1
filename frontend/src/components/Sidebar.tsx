import { Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Divider, Box, Typography } from '@mui/material';
import { Home as HomeIcon, Folder as FolderIcon, Settings as SettingsIcon, MenuBook as MenuBookIcon } from '@mui/icons-material';
import { Link, useLocation } from 'react-router-dom';
import { API_BASE_URL } from '../services/apiClient';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const location = useLocation();

  const navItems = [
    {
      text: 'Prompts',
      icon: <HomeIcon />,
      path: '/',
    },
    {
      text: 'Collections',
      icon: <FolderIcon />,
      path: '/collections',
    },
  ];

  return (
    <Drawer
      variant="temporary"
      open={open}
      onClose={onClose}
      ModalProps={{
        keepMounted: true,
      }}
      sx={{
        '& .MuiDrawer-paper': {
          width: 240,
          boxSizing: 'border-box',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" component="div" sx={{ mb: 2 }}>
          PromptLab
        </Typography>
        <Divider />
      </Box>
      <List>
        {navItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              onClick={onClose}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
        <ListItem disablePadding>
          <ListItemButton
            component="a"
            href={`${API_BASE_URL}/docs#/`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onClose}
          >
            <ListItemIcon><MenuBookIcon /></ListItemIcon>
            <ListItemText primary="Docs" />
          </ListItemButton>
        </ListItem>
      </List>
      <Divider sx={{ mt: 'auto' }} />
      <List>
        <ListItem disablePadding>
          <ListItemButton>
            <ListItemIcon>
              <SettingsIcon />
            </ListItemIcon>
            <ListItemText primary="Settings" />
          </ListItemButton>
        </ListItem>
      </List>
    </Drawer>
  );
}