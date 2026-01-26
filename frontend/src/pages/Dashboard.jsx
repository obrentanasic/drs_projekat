import React, { useState, useEffect } from 'react'
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  Person as PersonIcon,
  ExitToApp as LogoutIcon,
  Refresh as RefreshIcon,
  AdminPanelSettings as AdminIcon,
  Verified as VerifiedIcon,
  Edit as EditIcon,
  LocationOn as LocationIcon,
  CalendarToday as CalendarIcon,
  Email as EmailIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { userAPI } from '../services/api'

const Dashboard = () => {
  const { user, isAuthenticated, logout, isAdmin, isModerator } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    console.log('Dashboard mounted, user:', user?.email)
    
    if (!isAuthenticated || !user) {
      console.log(' Not authenticated, redirecting to login')
      navigate('/login')
      return
    }
    
    fetchDashboardData()
  }, [isAuthenticated, user, navigate])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError('')
      
      console.log(' Fetching dashboard data...')
      
      if (isAdmin()) {
        try {
          const statsRes = await userAPI.getUserStats()
          setStats(statsRes.data)
          console.log(' Admin stats received:', statsRes.data)
        } catch (statsErr) {
          console.warn(' Could not fetch admin stats:', statsErr.message)
          setStats({
            total_users: 0,
            players: 0,
            moderators: 0,
            admins: 0,
            blocked_users: 0,
            new_users_last_week: 0
          })
        }
      }
      
    } catch (err) {
      console.error(' Dashboard error:', err)
      
      const errorMessage = err.response?.data?.error || err.message || 'Failed to load dashboard'
      setError(errorMessage)
      
      if (err.response?.status === 401) {
        console.log(' 401 Unauthorized')
        setTimeout(() => navigate('/login'), 1500)
      }
      
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    console.log(' Logout initiated')
    await logout()
    navigate('/login')
  }

  const handleRefresh = () => {
    console.log(' Refreshing dashboard')
    fetchDashboardData()
  }

  const handleAdminPanel = () => {
    navigate('/admin')
  }

  const handleProfile = () => {
    navigate('/profile')
  }

 const handleBrowseQuizzes = () => {
    navigate('/quizzes')
  }

  const handleCreateQuiz = () => {
    navigate('/create-quiz')
  }


  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh" flexDirection="column">
        <CircularProgress size={80} thickness={4} />
        <Typography variant="h6" sx={{ mt: 4, color: 'primary.main' }}>
          Loading your dashboard...
        </Typography>
        <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>
          Welcome back, {user?.first_name || user?.email}!
        </Typography>
      </Box>
    )
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* HEADER */}
      <Paper 
        sx={{ 
          p: 4, 
          mb: 4, 
          background: 'linear-gradient(135deg, #1976d2 0%, #0d47a1 100%)',
          color: 'white',
          borderRadius: 3,
          boxShadow: 3
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={3}>
          <Box>
            <Typography variant="h3" fontWeight="bold" gutterBottom>
               Quiz Platform Dashboard
            </Typography>
            <Typography variant="h6" sx={{ opacity: 0.9, mb: 2 }}>
              Welcome back, {user?.first_name} {user?.last_name}!
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
              <Chip 
                icon={<VerifiedIcon />}
                label={`Role: ${user?.role || 'IGRAČ'}`} 
                sx={{ 
                  background: user?.role === 'ADMINISTRATOR' ? '#d32f2f' : 
                             user?.role === 'MODERATOR' ? '#ed6c02' : '#2e7d32',
                  color: 'white',
                  fontWeight: 'bold'
                }}
              />
              
              <Chip 
                label={`Email: ${user?.email}`} 
                sx={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
              
              {user?.profile_image && (
                <Chip 
                  label="Profile Picture ✓" 
                  sx={{ background: 'rgba(76, 175, 80, 0.3)', color: 'white' }}
                />
              )}
            </Box>
          </Box>
          
          <Box display="flex" gap={2} flexWrap="wrap">
            <Tooltip title="Refresh Dashboard">
              <IconButton 
                onClick={handleRefresh}
                sx={{ 
                  background: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  '&:hover': { background: 'rgba(255,255,255,0.3)' }
                }}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            
            <Button
              variant="contained"
              color="secondary"
              onClick={handleProfile}
              startIcon={<PersonIcon />}
              sx={{ 
                fontWeight: 'bold',
                borderRadius: 2,
                px: 3,
                background: 'rgba(255,255,255,0.9)',
                color: '#1976d2',
                '&:hover': {
                  background: 'white'
                }
              }}
            >
              My Profile
            </Button>
            
            <Button
              variant="contained"
              color="primary"
              onClick={handleBrowseQuizzes}
              startIcon={<EditIcon />}
              sx={{ 
                fontWeight: 'bold',
                borderRadius: 2,
                px: 3
              }}
            >
              Browse Quizzes
            </Button>

            {isModerator() && (
              <Button
                variant="contained"
                color="primary"
                onClick={handleCreateQuiz}
                startIcon={<EditIcon />}
                sx={{ 
                  fontWeight: 'bold',
                  borderRadius: 2,
                  px: 3
                }}
              >
                Create Quiz
              </Button>
            )}

            <Button
              variant="contained"
              color="error"
              onClick={handleLogout}
              startIcon={<LogoutIcon />}
              sx={{ 
                fontWeight: 'bold',
                borderRadius: 2,
                px: 3
              }}
            >
              Logout
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* ERROR DISPLAY */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 4, borderRadius: 2 }}
          action={
            <Button color="inherit" size="small" onClick={handleRefresh}>
              Retry
            </Button>
          }
        >
          <Typography variant="subtitle1" fontWeight="bold">Dashboard Error:</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      )}

      {/* USER PROFILE CARD */}
      <Grid container spacing={3} sx={{ mb: 6 }}>
        <Grid item xs={12} md={6}>
          <Card sx={{ borderRadius: 3, boxShadow: 2, height: '100%' }}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h5" fontWeight="bold" gutterBottom color="primary">
                <PersonIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Personal Information
              </Typography>
              <Divider sx={{ mb: 3 }} />
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PersonIcon fontSize="small" /> Full Name
                  </Typography>
                  <Typography variant="h6" fontWeight="medium">
                    {user?.first_name} {user?.last_name}
                  </Typography>
                </Box>
                
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <EmailIcon fontSize="small" /> Email Address
                  </Typography>
                  <Typography variant="h6" fontWeight="medium">
                    {user?.email}
                  </Typography>
                </Box>
                
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CalendarIcon fontSize="small" /> Date of Birth
                  </Typography>
                  <Typography variant="h6" fontWeight="medium">
                    {user?.date_of_birth ? new Date(user.date_of_birth).toLocaleDateString('en-GB') : 'Not specified'}
                  </Typography>
                </Box>
                
                {user?.country && (
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LocationIcon fontSize="small" /> Location
                    </Typography>
                    <Typography variant="h6" fontWeight="medium">
                      {user.country}
                      {user.street && `, ${user.street}`}
                      {user.number && ` ${user.number}`}
                    </Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ borderRadius: 3, boxShadow: 2, height: '100%' }}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h5" fontWeight="bold" gutterBottom color="primary">
                <VerifiedIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Account Information
              </Typography>
              <Divider sx={{ mb: 3 }} />
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">Account Role</Typography>
                  <Chip 
                    label={user?.role || 'IGRAČ'}
                    color={
                      user?.role === 'ADMINISTRATOR' ? 'error' :
                      user?.role === 'MODERATOR' ? 'warning' : 'success'
                    }
                    size="medium"
                    sx={{ fontSize: '1rem', fontWeight: 'bold', py: 1 }}
                  />
                </Box>
                
                <Box>
                  <Typography variant="body2" color="text.secondary">Account Created</Typography>
                  <Typography variant="h6" fontWeight="medium">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-GB') : 'N/A'}
                  </Typography>
                </Box>
                
                <Box>
                  <Typography variant="body2" color="text.secondary">Last Profile Update</Typography>
                  <Typography variant="h6" fontWeight="medium">
                    {user?.updated_at ? new Date(user.updated_at).toLocaleDateString('en-GB') : 'N/A'}
                  </Typography>
                </Box>
                
                <Box>
                  <Typography variant="body2" color="text.secondary">Account Status</Typography>
                  <Chip 
                    label={user?.is_blocked ? 'BLOCKED' : 'ACTIVE'}
                    color={user?.is_blocked ? 'error' : 'success'}
                    size="medium"
                    sx={{ fontSize: '1rem', fontWeight: 'bold', py: 1 }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* ADMIN PANEL CARD (samo za admina) */}
      {isAdmin() && (
        <Paper sx={{ p: 4, mb: 6, borderRadius: 3, boxShadow: 2 }}>
          <Box display="flex" alignItems="center" mb={3}>
            <AdminIcon sx={{ mr: 2, fontSize: 40, color: 'primary.main' }} />
            <Typography variant="h4" fontWeight="bold">
              Administrator Panel
            </Typography>
          </Box>
          
          <Divider sx={{ mb: 4 }} />
          
          <Grid container spacing={3}>
            {stats ? (
              <>
                <Grid item xs={6} sm={4} md={2}>
                  <Card sx={{ borderRadius: 2 }}>
                    <CardContent sx={{ textAlign: 'center', p: 3 }}>
                      <Typography variant="h3" fontWeight="bold" color="primary">
                        {stats.total_users}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Users
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={6} sm={4} md={2}>
                  <Card sx={{ borderRadius: 2 }}>
                    <CardContent sx={{ textAlign: 'center', p: 3 }}>
                      <Typography variant="h3" fontWeight="bold" color="success.main">
                        {stats.players}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Players
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={6} sm={4} md={2}>
                  <Card sx={{ borderRadius: 2 }}>
                    <CardContent sx={{ textAlign: 'center', p: 3 }}>
                      <Typography variant="h3" fontWeight="bold" color="warning.main">
                        {stats.moderators}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Moderators
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={6} sm={4} md={2}>
                  <Card sx={{ borderRadius: 2 }}>
                    <CardContent sx={{ textAlign: 'center', p: 3 }}>
                      <Typography variant="h3" fontWeight="bold" color="error.main">
                        {stats.admins}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Admins
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </>
            ) : (
              <Grid item xs={12}>
                <Typography variant="body1" color="text.secondary" align="center">
                  Loading platform statistics...
                </Typography>
              </Grid>
            )}
            
            <Grid item xs={12} sx={{ mt: 3 }}>
              <Button
                variant="contained"
                color="error"
                size="large"
                fullWidth
                onClick={handleAdminPanel}
                startIcon={<AdminIcon />}
                sx={{ py: 2, fontWeight: 'bold', borderRadius: 2 }}
              >
                Go to Admin Panel
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}
      
      {/* FOOTER JE UKLONJEN */}
    </Container>
  )
}

export default Dashboard