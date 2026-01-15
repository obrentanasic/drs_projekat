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
  const [showPassword, setShowPassword] = useState(false)
  
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!email || !password) {
      setError('Molimo unesite sve podatke')
      return
    }
    
    console.log(' LOGIN ATTEMPT:', email)
    setLoading(true)
    setError('')
    setBlockedInfo(null)
    
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
          setError('Nalog je privremeno blokiran zbog previše neuspešnih pokušaja')
        } else {
          // OVO JE KLJUČNA PROMENA: Prikazujemo samo osnovnu grešku
          setError(result.error || 'Pogrešan email ili lozinka')
        }
      }
      
    } catch (err) {
      console.error(' LOGIN ERROR:', err)
      setError(err.message || 'Došlo je do greške. Pokušajte ponovo.')
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
            Distribuirani računarski sistemi 2025/2026
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Prijavite se za pristup platformi
          </Typography>
        </Box>

        {/* BLOCKED ACCOUNT WARNING - OVAJ DEO OSTAJEMO */}
        {blockedInfo && (
          <Alert 
            severity="warning" 
            icon={<WarningIcon />}
            sx={{ mb: 3, borderRadius: 2 }}
            onClose={() => setBlockedInfo(null)}
          >
            <Typography variant="subtitle2" fontWeight="bold">
              Nalog privremeno blokiran
            </Typography>
            <Typography variant="body2">
              Previše neuspešnih pokušaja. Nalog je blokiran na {formatBlockedTime(blockedInfo.remaining)} minuta.
            </Typography>
          </Alert>
        )}

        {/* OVO JE UKLONJENO:
          1. ATTEMPTS LEFT WARNING (ceo Alert komponent)
          2. Poruke "Login Failed", "Attempts remaining", "After 3 failed attempts"
        */}

        {/* ERROR DISPLAY - OVO OSTAJEMO, ALI BEZ "Login Error:" naslova */}
        {error && !blockedInfo && (
          <Alert 
            severity="error" 
            sx={{ mb: 3, borderRadius: 2 }}
            onClose={() => setError('')}
          >
            <Typography variant="body2">
              {error}
            </Typography>
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Email adresa"
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
            label="Lozinka"
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
            {loading ? 'Prijavljivanje...' : blockedInfo ? 'Nalog blokiran' : 'Prijavi se'}
          </Button>
        </form>

        <Divider sx={{ my: 3 }}>
          <Typography variant="body2" color="textSecondary">
            ILI
          </Typography>
        </Divider>

        <Box textAlign="center">
          <Typography variant="body1" color="textSecondary" gutterBottom>
            Nemate nalog?
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
            Kreiraj novi nalog
          </Button>
        </Box>
      </Paper>
    </Container>
  )
}

export default Login