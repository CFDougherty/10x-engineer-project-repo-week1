import { AppBar, Toolbar, Typography, Button, IconButton, Tooltip } from '@mui/material';
import { Link } from 'react-router-dom';
import { Menu as MenuIcon, SettingsApplications } from '@mui/icons-material';

interface HeaderProps {
  onMenuClick?: () => void;
  isMobile?: boolean;
  onAdminClick?: () => void;
}

export default function Header({ onMenuClick, isMobile = false, onAdminClick }: HeaderProps) {
  return (
    <AppBar position="static">
      <Toolbar>
        {isMobile && onMenuClick && (
          <IconButton
            color="inherit"
            edge="start"
            onClick={onMenuClick}
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
        {onAdminClick && (
          <Tooltip title="Admin Tools">
            <IconButton color="inherit" onClick={onAdminClick} sx={{ color: 'error.main' }}>
              <SettingsApplications />
            </IconButton>
          </Tooltip>
        )}
      </Toolbar>
    </AppBar>
  );
}