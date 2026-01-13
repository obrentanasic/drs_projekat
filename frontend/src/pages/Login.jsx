import React, { useState } from 'react'
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
  Divider,
  InputAdornment,
  IconButton,
} from '@mui/material'
import {
  Email as EmailIcon,
  Lock as LockIcon,
  Visibility,
  VisibilityOff,
  Login as LoginIcon,
  PersonAdd as PersonAddIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [blockedInfo, setBlockedInfo] = useState(null)
  const [attemptsLeft, setAttemptsLeft] = useState(null)
  const [showPassword, setShowPassword] = useState(false)
  
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!email || !password) {
      setError('Please fill in all fields')
      return
    }
    
    console.log(' LOGIN ATTEMPT:', email)
    setLoading(true)
    setError('')
    setBlockedInfo(null)
    setAttemptsLeft(null)
    
    try {
      const result = await login(email, password)
      
      console.log(' Login result from context:', result)
      
      if (result.success) {
        console.log(' LOGIN SUCCESS via Context, redirecting...')
        navigate('/dashboard', { replace: true })
      } else {
        if (result.blocked) {
          setBlockedInfo({
            until: result.blocked_until,
            remaining: result.remaining_seconds
          })
          setError('Account temporarily blocked due to too many failed attempts')
        } else if (result.attempts_left !== undefined) {
          setAttemptsLeft(result.attempts_left)
          setError(result.error || 'Invalid credentials')
        } else {
          setError(result.error || 'Login failed')
        }
      }
      
    } catch (err) {
      console.error(' LOGIN ERROR:', err)
      setError(err.message || 'An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const formatBlockedTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Paper 
        elevation={6} 
        sx={{ 
          p: 5, 
          borderRadius: 3,
          background: 'linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%)'
        }}
      >
        <Box textAlign="center" mb={4}>
          <Typography variant="h3" fontWeight="bold" gutterBottom color="primary">
             Quiz Platform
          </Typography>
          <Typography variant="h5" color="textSecondary" gutterBottom>
            Distributed Systems Project 2025/2026
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Sign in to access the platform
          </Typography>
        </Box>

        {/* BLOCKED ACCOUNT WARNING */}
        {blockedInfo && (
          <Alert 
            severity="warning" 
            icon={<WarningIcon />}
            sx={{ mb: 3, borderRadius: 2 }}
            onClose={() => setBlockedInfo(null)}
          >
            <Typography variant="subtitle2" fontWeight="bold">
              Account Temporarily Blocked
            </Typography>
            <Typography variant="body2">
              Too many failed login attempts. Account is blocked for {formatBlockedTime(blockedInfo.remaining)} minutes.
            </Typography>
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Blocked until: {new Date(blockedInfo.until).toLocaleTimeString()}
            </Typography>
          </Alert>
        )}

        {/* ATTEMPTS LEFT WARNING */}
        {attemptsLeft !== null && (
          <Alert 
            severity="info"
            sx={{ mb: 3, borderRadius: 2 }}
            onClose={() => setAttemptsLeft(null)}
          >
            <Typography variant="subtitle2" fontWeight="bold">
              Login Failed
            </Typography>
            <Typography variant="body2">
              Attempts remaining: <strong>{attemptsLeft}</strong>
            </Typography>
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              After 3 failed attempts, account will be blocked for 1 minute.
            </Typography>
          </Alert>
        )}

        {/* ERROR DISPLAY */}
        {error && !blockedInfo && (
          <Alert 
            severity="error" 
            sx={{ mb: 3, borderRadius: 2 }}
            onClose={() => setError('')}
          >
            <Typography variant="subtitle2" fontWeight="bold">
              Login Error:
            </Typography>
            <Typography variant="body2">
              {error}
            </Typography>
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            margin="normal"
            variant="outlined"
            required
            disabled={loading || (blockedInfo !== null)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <EmailIcon color="action" />
                </InputAdornment>
              ),
            }}
            sx={{ mb: 3 }}
          />

          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            variant="outlined"
            required
            disabled={loading || (blockedInfo !== null)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LockIcon color="action" />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                    disabled={loading || (blockedInfo !== null)}
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ mb: 4 }}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={loading || (blockedInfo !== null)}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <LoginIcon />}
            sx={{
              py: 1.5,
              mb: 3,
              borderRadius: 2,
              fontWeight: 'bold',
              fontSize: '1.1rem',
              backgroundColor: blockedInfo ? 'grey.500' : 'primary.main',
              '&:hover': {
                backgroundColor: blockedInfo ? 'grey.600' : 'primary.dark',
              }
            }}
          >
            {loading ? 'Signing In...' : blockedInfo ? 'Account Blocked' : 'Sign In'}
          </Button>
        </form>

        <Divider sx={{ my: 3 }}>
          <Typography variant="body2" color="textSecondary">
            OR
          </Typography>
        </Divider>

        <Box textAlign="center">
          <Typography variant="body1" color="textSecondary" gutterBottom>
            Don't have an account?
          </Typography>
          <Button
            component={RouterLink}
            to="/register"
            variant="outlined"
            size="large"
            startIcon={<PersonAddIcon />}
            sx={{ 
              mt: 1,
              borderRadius: 2,
              px: 4
            }}
          >
            Create New Account
          </Button>
        </Box>
      </Paper>
    </Container>
  )
}

export default Login