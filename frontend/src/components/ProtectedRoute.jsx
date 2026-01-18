import React from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { CircularProgress, Box, Typography } from '@mui/material'

const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  console.log(' ProtectedRoute state:', {
    isAuthenticated,
    isLoading,
    user: user?.email,
    path: location.pathname
  })

  if (isLoading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="60vh"
        flexDirection="column"
        gap={3}
      >
        <CircularProgress size={60} />
        <Typography variant="h6" color="primary">
          Checking authentication...
        </Typography>
      </Box>
    )
  }

  // Ako korisnik nije autentifikovan, redirect na login
  if (!isAuthenticated || !user) {
    console.log(' ProtectedRoute: User not authenticated, redirecting to login')
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  // Provera uloge ako je specificirana
  if (requiredRole) {
    const roleHierarchy = {
      'IGRAČ': 1,
      'MODERATOR': 2,
      'ADMINISTRATOR': 3
    }

    const userRoleValue = roleHierarchy[user.role] || 0
    const requiredRoleValue = roleHierarchy[requiredRole] || 0

    // ADMIN ima pristup svemu
    if (user.role === 'ADMINISTRATOR') {
      // Admin može pristupiti svim stranicama
    }
    // MODERATOR može pristupiti svojim i player stranicama
    else if (user.role === 'MODERATOR' && requiredRoleValue <= 2) {
      // Moderator može pristupiti
    }
    // IGRAČ može pristupiti samo player stranicama
    else if (user.role === 'IGRAČ' && requiredRoleValue <= 1) {
      // Player može pristupiti
    }
    // Ako nema odgovarajuću ulogu
    else {
      console.log(` ProtectedRoute: User role ${user.role} insufficient for ${requiredRole}`)
      
      return (
        <Box 
          display="flex" 
          justifyContent="center" 
          alignItems="center" 
          minHeight="60vh"
          flexDirection="column"
          gap={3}
          p={4}
        >
          <Typography variant="h4" color="error" fontWeight="bold">
             Access Denied
          </Typography>
          <Typography variant="h6" color="text.secondary" align="center">
            You don't have permission to access this page.
          </Typography>
          <Typography variant="body1" color="text.secondary" align="center">
            Required role: <strong>{requiredRole}</strong><br/>
            Your role: <strong>{user.role}</strong>
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
            Contact an administrator if you believe this is an error.
          </Typography>
        </Box>
      )
    }
  }

  // Ako je blokiran korisnik
  if (user.is_blocked) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="60vh"
        flexDirection="column"
        gap={3}
        p={4}
      >
        <Typography variant="h4" color="error" fontWeight="bold">
           Account Blocked
        </Typography>
        <Typography variant="h6" color="text.secondary" align="center">
          Your account has been temporarily blocked.
        </Typography>
        <Typography variant="body1" color="text.secondary" align="center">
          Reason: Too many failed login attempts
        </Typography>
        {user.blocked_until && (
          <Typography variant="body2" color="text.secondary" align="center">
            Blocked until: {new Date(user.blocked_until).toLocaleString()}
          </Typography>
        )}
      </Box>
    )
  }

  return children ? children : <Outlet />
}

export default ProtectedRoute