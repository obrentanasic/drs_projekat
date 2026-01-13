import React, { useState } from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  useMediaQuery,
  useTheme,
  Chip,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Person as PersonIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const Navbar = () => {
  const [anchorEl, setAnchorEl] = useState(null)
  const [mobileMenuAnchor, setMobileMenuAnchor] = useState(null)
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMobileMenuOpen = (event) => {
    setMobileMenuAnchor(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setMobileMenuAnchor(null)
  }

  const handleLogout = () => {
    logout()
    handleMenuClose()
    navigate('/login')
  }

  const handleNavigation = (path) => {
    navigate(path)
    handleMenuClose()
  }

  if (location.pathname === '/login' || location.pathname === '/register') {
    return null
  }

  if (!isAuthenticated || !user) {
    return null
  }

  const userInitials = `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()

  return (
    <>
      <AppBar 
        position="static" 
        elevation={0}
        sx={{ 
          backgroundColor: 'transparent',
          color: 'text.primary',
          boxShadow: 'none',
          borderBottom: '1px solid #e0e0e0',
          background: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(8px)'
        }}
      >
        <Toolbar sx={{ justifyContent: 'flex-end', minHeight: '64px' }}>
          {/* User Section */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* User Info - Desktop */}
            {!isMobile && (
              <>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar
                    sx={{ 
                      width: 36, 
                      height: 36, 
                      bgcolor: 'primary.main',
                      cursor: 'pointer'
                    }}
                    onClick={handleProfileMenuOpen}
                  >
                    {userInitials}
                  </Avatar>
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {user.first_name} {user.last_name}
                    </Typography>
                    <Chip 
                      label={user.role}
                      size="small"
                      sx={{ 
                        height: 20,
                        fontSize: '0.65rem',
                        bgcolor: user.role === 'ADMINISTRATOR' ? '#d32f2f' : 
                                 user.role === 'MODERATOR' ? '#ed6c02' : '#2e7d32',
                        color: 'white'
                      }}
                    />
                  </Box>
                </Box>
              </>
            )}

            {/* Mobile Menu Button */}
            {isMobile && (
              <>
                <IconButton
                  color="inherit"
                  onClick={handleMobileMenuOpen}
                  sx={{ mr: 1 }}
                >
                  <MenuIcon />
                </IconButton>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar
                    sx={{ 
                      width: 32, 
                      height: 32, 
                      bgcolor: 'primary.main'
                    }}
                  >
                    {userInitials}
                  </Avatar>
                </Box>
              </>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      {/* Mobile Menu */}
      <Menu
        anchorEl={mobileMenuAnchor}
        open={Boolean(mobileMenuAnchor)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: { width: 280, maxWidth: '100%' }
        }}
      >
        {/* User Info */}
        <MenuItem disabled sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 40, height: 40 }}>
              {userInitials}
            </Avatar>
            <Box>
              <Typography variant="subtitle2" fontWeight="bold">
                {user.first_name} {user.last_name}
            </Typography>
              <Typography variant="caption" color="text.secondary" display="block">
                {user.email}
              </Typography>
              <Chip 
                label={user.role}
                size="small"
                sx={{ 
                  mt: 0.5,
                  height: 18,
                  fontSize: '0.6rem',
                  bgcolor: user.role === 'ADMINISTRATOR' ? '#d32f2f' : 
                           user.role === 'MODERATOR' ? '#ed6c02' : '#2e7d32',
                  color: 'white'
                }}
              />
            </Box>
          </Box>
        </MenuItem>
        
        <Divider />
        
        {/* Profile & Logout */}
        <MenuItem onClick={() => handleNavigation('/profile')}>
          <PersonIcon fontSize="small" sx={{ mr: 2 }} />
          My Profile
        </MenuItem>
        
        <MenuItem onClick={handleLogout}>
          <LogoutIcon fontSize="small" sx={{ mr: 2 }} />
          Logout
        </MenuItem>
      </Menu>

      {/* Profile Menu (Desktop) */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: { width: 200 }
        }}
      >
        <MenuItem onClick={() => handleNavigation('/profile')}>
          <PersonIcon fontSize="small" sx={{ mr: 2 }} />
          My Profile
        </MenuItem>
        
        <Divider />
        
        <MenuItem onClick={handleLogout}>
          <LogoutIcon fontSize="small" sx={{ mr: 2 }} />
          Logout
        </MenuItem>
      </Menu>
    </>
  )
}

export default Navbar