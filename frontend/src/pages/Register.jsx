import React, { useState } from 'react'
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  Link,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Grid,
  InputAdornment,
  IconButton,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material'
import {
  Person as PersonIcon,
  Email as EmailIcon,
  Lock as LockIcon,
  Visibility,
  VisibilityOff,
  HowToReg as RegisterIcon,
  ArrowBack as ArrowBackIcon,
  Cake as CakeIcon,
  Transgender as GenderIcon,
  Flag as CountryIcon,
  Home as StreetIcon,
  Numbers as NumberIcon,
} from '@mui/icons-material'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { authService } from '../services/auth'

const Register = () => {
  const navigate = useNavigate()
  const [activeStep, setActiveStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  const [formData, setFormData] = useState({
    // Obavezna polja
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    date_of_birth: null,
    
    // Opciona polja
    gender: '',
    country: '',
    street: '',
    number: ''
  })
  
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const steps = ['Personal Information', 'Account Details', 'Confirmation']

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleDateChange = (date) => {
    setFormData(prev => ({
      ...prev,
      date_of_birth: date
    }))
  }

  const handleNext = () => {
    setError('')
    
    // Validacija za prvi korak
    if (activeStep === 0) {
      if (!formData.first_name || !formData.last_name) {
        setError('Please fill in first name and last name')
        return
      }
      
      if (formData.first_name.length < 2 || formData.last_name.length < 2) {
        setError('Names must be at least 2 characters long')
        return
      }
      
      if (!formData.date_of_birth) {
        setError('Date of birth is required')
        return
      }
      
      const today = new Date()
      const birthDate = new Date(formData.date_of_birth)
      const age = today.getFullYear() - birthDate.getFullYear()
      const monthDiff = today.getMonth() - birthDate.getMonth()
      
      if (age < 13 || (age === 13 && monthDiff < 0)) {
        setError('You must be at least 13 years old to register')
        return
      }
    }
    
    // Validacija za drugi korak
    if (activeStep === 1) {
      if (!formData.email) {
        setError('Email is required')
        return
      }
      
      // Proveri email format
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(formData.email)) {
        setError('Please enter a valid email address')
        return
      }
      
      if (!formData.password || !formData.confirmPassword) {
        setError('Please fill in password fields')
        return
      }
      
      if (formData.password.length < 8) {
        setError('Password must be at least 8 characters long')
        return
      }
      
      if (!/[A-Z]/.test(formData.password)) {
        setError('Password must contain at least one uppercase letter')
        return
      }
      
      if (!/[a-z]/.test(formData.password)) {
        setError('Password must contain at least one lowercase letter')
        return
      }
      
      if (!/\d/.test(formData.password)) {
        setError('Password must contain at least one number')
        return
      }
      
      if (formData.password !== formData.confirmPassword) {
        setError('Passwords do not match')
        return
      }
    }
    
    setActiveStep((prevStep) => prevStep + 1)
  }

  const handleBack = () => {
    setError('')
    setActiveStep((prevStep) => prevStep - 1)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (activeStep !== steps.length - 1) {
      handleNext()
      return
    }
    
    console.log('📝 REGISTRATION ATTEMPT:', { 
      email: formData.email,
      first_name: formData.first_name,
      last_name: formData.last_name
    })
    
    setLoading(true)
    setError('')
    setSuccess('')
    
    try {
      const userData = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        email: formData.email.toLowerCase().trim(),
        password: formData.password,
        date_of_birth: formData.date_of_birth.toISOString().split('T')[0], // YYYY-MM-DD
        gender: formData.gender || null,
        country: formData.country || null,
        street: formData.street || null,
        number: formData.number || null
      }
      
      console.log('📤 Sending registration data:', userData)
      
      const result = await authService.register(userData)
      
      if (result.success) {
        console.log('✅ REGISTRATION SUCCESS:', result.user)
        
        setSuccess('Registration successful! You are now logged in. Redirecting to dashboard...')
        
        setTimeout(() => {
          navigate('/dashboard')
        }, 2000)
      } else {
        throw new Error(result.error || 'Registration failed')
      }
      
    } catch (err) {
      console.error(' REGISTRATION ERROR:', err)
      
      const errorMessage = err.response?.data?.error || 
                          err.response?.data?.message || 
                          err.message || 
                          'Registration failed'
      
      const errorDetails = err.response?.data?.details || ''
      setError(`${errorMessage} ${errorDetails ? `(${errorDetails})` : ''}`)
      
    } finally {
      setLoading(false)
    }
  }

  const getStepContent = (step) => {
    switch (step) {
      case 0: // Personal Information
        return (
          <Box>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  margin="normal"
                  variant="outlined"
                  required
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PersonIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  margin="normal"
                  variant="outlined"
                  required
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PersonIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
            </Grid>
            
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="Date of Birth"
                value={formData.date_of_birth}
                onChange={handleDateChange}
                disableFuture
                maxDate={new Date(new Date().setFullYear(new Date().getFullYear() - 13))}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    fullWidth
                    margin="normal"
                    required
                    disabled={loading}
                    InputProps={{
                      ...params.InputProps,
                      startAdornment: (
                        <InputAdornment position="start">
                          <CakeIcon color="action" />
                        </InputAdornment>
                      ),
                    }}
                  />
                )}
              />
            </LocalizationProvider>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Gender</InputLabel>
              <Select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                label="Gender"
                disabled={loading}
                startAdornment={
                  <InputAdornment position="start">
                    <GenderIcon color="action" />
                  </InputAdornment>
                }
              >
                <MenuItem value=""><em>Select Gender</em></MenuItem>
                <MenuItem value="M">Male</MenuItem>
                <MenuItem value="F">Female</MenuItem>
                <MenuItem value="O">Other</MenuItem>
                <MenuItem value="N">Prefer not to say</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              fullWidth
              label="Country"
              name="country"
              value={formData.country}
              onChange={handleChange}
              margin="normal"
              variant="outlined"
              disabled={loading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <CountryIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        )
      
      case 1: // Account Details
        return (
          <Box>
            <TextField
              fullWidth
              label="Email Address"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              margin="normal"
              variant="outlined"
              required
              disabled={loading}
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
              name="password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleChange}
              margin="normal"
              variant="outlined"
              required
              disabled={loading}
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
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 3 }}
            />
            
            <TextField
              fullWidth
              label="Confirm Password"
              name="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={handleChange}
              margin="normal"
              variant="outlined"
              required
              disabled={loading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon color="action" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      edge="end"
                    >
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />
            
            <Box sx={{ mt: 3, p: 2, bgcolor: '#f5f5f5', borderRadius: 2 }}>
              <Typography variant="body2" fontWeight="bold" gutterBottom>
                Password Requirements (as per specification):
              </Typography>
              <Typography variant="body2" color="textSecondary">
                • Minimum 8 characters<br/>
                • At least one uppercase letter (A-Z)<br/>
                • At least one lowercase letter (a-z)<br/>
                • At least one number (0-9)<br/>
                • Passwords will be securely hashed (never stored in plain text)
              </Typography>
            </Box>
          </Box>
        )
      
      case 2: // Address & Confirmation
        return (
          <Box>
            <TextField
              fullWidth
              label="Street Address"
              name="street"
              value={formData.street}
              onChange={handleChange}
              margin="normal"
              variant="outlined"
              disabled={loading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <StreetIcon color="action" />
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 3 }}
            />
            
            <TextField
              fullWidth
              label="Street Number"
              name="number"
              value={formData.number}
              onChange={handleChange}
              margin="normal"
              variant="outlined"
              disabled={loading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <NumberIcon color="action" />
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 3 }}
            />
            
            <Box sx={{ mt: 3, p: 3, bgcolor: '#f0f7ff', borderRadius: 2, border: '1px solid #e0e0e0' }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom color="primary">
                Registration Summary
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Name:</Typography>
                  <Typography variant="body1">{formData.first_name} {formData.last_name}</Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Email:</Typography>
                  <Typography variant="body1">{formData.email}</Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Date of Birth:</Typography>
                  <Typography variant="body1">
                    {formData.date_of_birth ? formData.date_of_birth.toLocaleDateString() : 'Not provided'}
                  </Typography>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">Role:</Typography>
                  <Typography variant="body1" fontWeight="bold">IGRAČ (Default)</Typography>
                </Grid>
                
                {formData.country && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="textSecondary">Location:</Typography>
                    <Typography variant="body1">
                      {formData.country}
                      {formData.street && `, ${formData.street}`}
                      {formData.number && ` ${formData.number}`}
                    </Typography>
                  </Grid>
                )}
              </Grid>
              
              <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                Note: After registration, your role will be "IGRAČ" by default. 
                To become a MODERATOR, contact an ADMINISTRATOR.
              </Typography>
            </Box>
          </Box>
        )
      
      default:
        return 'Unknown step'
    }
  }

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Paper 
        elevation={6} 
        sx={{ 
          p: { xs: 3, md: 5 }, 
          borderRadius: 3,
          background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)'
        }}
      >
        <Button
          component={RouterLink}
          to="/login"
          startIcon={<ArrowBackIcon />}
          sx={{ mb: 4 }}
        >
          Back to Login
        </Button>

        <Box textAlign="center" mb={4}>
          <Typography variant="h3" fontWeight="bold" gutterBottom color="primary">
            Create New Account
          </Typography>
          <Typography variant="h6" color="textSecondary" gutterBottom>
            Join our Quiz Platform - Distributed Systems Project 2025/2026
          </Typography>
          <Typography variant="body2" color="textSecondary">
            All fields marked with * are required
          </Typography>
        </Box>

        {/* Stepper */}
        <Stepper activeStep={activeStep} sx={{ mb: 5 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {/* ERROR DISPLAY */}
        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 3, borderRadius: 2 }}
            onClose={() => setError('')}
          >
            <Typography variant="subtitle2" fontWeight="bold">
              Registration Error:
            </Typography>
            <Typography variant="body2">
              {error}
            </Typography>
          </Alert>
        )}

        {/* SUCCESS DISPLAY */}
        {success && (
          <Alert 
            severity="success" 
            sx={{ mb: 3, borderRadius: 2 }}
          >
            <Typography variant="subtitle2" fontWeight="bold">
              Success!
            </Typography>
            <Typography variant="body2">
              {success}
            </Typography>
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          {getStepContent(activeStep)}
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 5 }}>
            <Button
              onClick={handleBack}
              disabled={activeStep === 0 || loading}
              startIcon={<ArrowBackIcon />}
            >
              Back
            </Button>
            
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={loading}
              startIcon={
                loading ? (
                  <CircularProgress size={20} color="inherit" />
                ) : activeStep === steps.length - 1 ? (
                  <RegisterIcon />
                ) : null
              }
              sx={{
                px: 4,
                borderRadius: 2,
                fontWeight: 'bold'
              }}
            >
              {loading 
                ? 'Processing...' 
                : activeStep === steps.length - 1 
                  ? 'Complete Registration' 
                  : 'Next Step'
              }
            </Button>
          </Box>
        </form>

        {/* DEMO ACCOUNTS */}
        <Box sx={{ mt: 6, p: 3, bgcolor: '#f0f7ff', borderRadius: 2 }}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom color="primary">
             Quick Test Accounts (From Backend)
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            These accounts are created by the backend on startup:
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Paper sx={{ p: 2, bgcolor: 'white', borderRadius: 2, border: '2px solid #1976d2' }}>
                <Typography variant="body2" fontWeight="bold" color="primary">ADMINISTRATOR</Typography>
                <Typography variant="caption" display="block">admin@quizplatform.com</Typography>
                <Typography variant="caption" display="block">Password: Admin123!</Typography>
                <Typography variant="caption" color="textSecondary">Full admin privileges</Typography>
              </Paper>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <Paper sx={{ p: 2, bgcolor: 'white', borderRadius: 2, border: '2px solid #2e7d32' }}>
                <Typography variant="body2" fontWeight="bold" color="success.main">MODERATOR</Typography>
                <Typography variant="caption" display="block">moderator@quizplatform.com</Typography>
                <Typography variant="caption" display="block">Password: Moderator123!</Typography>
                <Typography variant="caption" color="textSecondary">Can create quizzes</Typography>
              </Paper>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <Paper sx={{ p: 2, bgcolor: 'white', borderRadius: 2, border: '2px solid #ed6c02' }}>
                <Typography variant="body2" fontWeight="bold" color="warning.main">IGRAČ</Typography>
                <Typography variant="caption" display="block">player@quizplatform.com</Typography>
                <Typography variant="caption" display="block">Password: Player123!</Typography>
                <Typography variant="caption" color="textSecondary">Default role</Typography>
              </Paper>
            </Grid>
          </Grid>
          
          <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
            Note: After 3 failed login attempts, account will be blocked for 1 minute (as per specification).
          </Typography>
        </Box>

        <Box textAlign="center" sx={{ mt: 4 }}>
          <Typography variant="body2" color="textSecondary">
            Already have an account?{' '}
            <Link component={RouterLink} to="/login" fontWeight="bold">
              Sign in here
            </Link>
          </Typography>
          
          <Typography variant="caption" color="textSecondary" display="block" sx={{ mt: 2 }}>
            Project: Distribuirani računarski sistemi 2025/2026 • Quiz Platform
          </Typography>
        </Box>
      </Paper>
    </Container>
  )
}

export default Register