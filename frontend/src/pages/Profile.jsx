import React, { useState, useEffect } from 'react'
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
  Grid,
  Avatar,
  IconButton,
  InputAdornment,
  MenuItem,
  Card,
  CardContent,
  Divider,
  Chip,
} from '@mui/material'
import {
  Person as PersonIcon,
  Email as EmailIcon,
  Cake as CakeIcon,
  Transgender as GenderIcon,
  Flag as CountryIcon,
  Home as StreetIcon,
  Numbers as NumberIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  CameraAlt as CameraIcon,
  ArrowBack as ArrowBackIcon,
  Verified as VerifiedIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'

const Profile = () => {
  const { user, updateProfile, uploadProfileImage, logout } = useAuth()
  const navigate = useNavigate()
  
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    date_of_birth: null,
    gender: '',
    country: '',
    street: '',
    number: '',
  })
  
  const [originalData, setOriginalData] = useState({})
  const [profileImage, setProfileImage] = useState(null)
  const [imagePreview, setImagePreview] = useState('')

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    
    console.log(' Loading profile for:', user.email)
    
    const userData = {
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      email: user.email || '',
      date_of_birth: user.date_of_birth ? new Date(user.date_of_birth) : null,
      gender: user.gender || '',
      country: user.country || '',
      street: user.street || '',
      number: user.number || '',
    }
    
    setFormData(userData)
    setOriginalData(userData)
    
    // Učitaj profilnu sliku ako postoji
    if (user.profile_image) {
      setImagePreview(`${import.meta.env.VITE_API_URL}/uploads/profile-pictures/${user.profile_image}`)
    }
  }, [user, navigate])

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

  const handleImageChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    // Validacija
    if (file.size > 5 * 1024 * 1024) { // 5MB
      setError('Image size must be less than 5MB')
      return
    }
    
    if (!file.type.match('image.*')) {
      setError('Please select an image file')
      return
    }
    
    setProfileImage(file)
    
    // Preview
    const reader = new FileReader()
    reader.onloadend = () => {
      setImagePreview(reader.result)
    }
    reader.readAsDataURL(file)
  }

  const handleUploadImage = async () => {
    if (!profileImage) {
      setError('Please select an image first')
      return
    }
    
    setUploading(true)
    setError('')
    setSuccess('')
    
    try {
      await uploadProfileImage(profileImage)
      setSuccess('Profile image uploaded successfully!')
      setProfileImage(null)
    } catch (err) {
      setError(err.message || 'Failed to upload image')
    } finally {
      setUploading(false)
    }
  }

  const handleSave = async () => {
    // Validacija
    if (!formData.first_name || !formData.last_name) {
      setError('First name and last name are required')
      return
    }
    
    if (!formData.date_of_birth) {
      setError('Date of birth is required')
      return
    }
    
    setLoading(true)
    setError('')
    setSuccess('')
    
    try {
      // Pripremi podatke za backend
      const updateData = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        date_of_birth: formData.date_of_birth.toISOString().split('T')[0],
        gender: formData.gender || null,
        country: formData.country || null,
        street: formData.street || null,
        number: formData.number || null,
      }
      
      await updateProfile(updateData)
      setSuccess('Profile updated successfully!')
      setOriginalData(formData)
      setIsEditing(false)
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setFormData(originalData)
    setError('')
    setIsEditing(false)
  }

  const handleBack = () => {
    navigate('/dashboard')
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  if (!user) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    )
  }

  const hasChanges = JSON.stringify(formData) !== JSON.stringify(originalData)

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* HEADER */}
      <Paper 
        sx={{ 
          p: 4, 
          mb: 4, 
          background: 'linear-gradient(135deg, #6a11cb 0%, #2575fc 100%)',
          color: 'white',
          borderRadius: 3,
          boxShadow: 3
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={3}>
          <Box display="flex" alignItems="center" gap={3}>
            <IconButton onClick={handleBack} sx={{ color: 'white' }}>
              <ArrowBackIcon />
            </IconButton>
            
            <Box>
              <Typography variant="h3" fontWeight="bold" gutterBottom>
                👤 User Profile
              </Typography>
              <Typography variant="h6" sx={{ opacity: 0.9 }}>
                Manage your personal information and account settings
              </Typography>
            </Box>
          </Box>
          
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              sx={{ 
                color: 'white', 
                borderColor: 'white',
                '&:hover': { borderColor: 'white', background: 'rgba(255,255,255,0.1)' }
              }}
              onClick={handleBack}
            >
              Back to Dashboard
            </Button>
            
            <Button
              variant="contained"
              color="error"
              onClick={handleLogout}
              sx={{ 
                background: 'rgba(255,255,255,0.9)',
                color: '#d32f2f',
                '&:hover': { background: 'white' }
              }}
            >
              Logout
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* ERROR & SUCCESS */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 4, borderRadius: 2 }}
          onClose={() => setError('')}
        >
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert 
          severity="success" 
          sx={{ mb: 4, borderRadius: 2 }}
          onClose={() => setSuccess('')}
        >
          {success}
        </Alert>
      )}

      <Grid container spacing={4}>
        {/* LEFT COLUMN - PROFILE IMAGE & INFO */}
        <Grid item xs={12} md={4}>
          <Card sx={{ borderRadius: 3, boxShadow: 2 }}>
            <CardContent sx={{ p: 4, textAlign: 'center' }}>
              {/* AVATAR */}
              <Box sx={{ position: 'relative', display: 'inline-block', mb: 3 }}>
                <Avatar
                  src={imagePreview}
                  sx={{ 
                    width: 150, 
                    height: 150,
                    border: '4px solid',
                    borderColor: 'primary.main',
                    mb: 2
                  }}
                >
                  {user.first_name?.[0]}{user.last_name?.[0]}
                </Avatar>
                
                <IconButton
                  component="label"
                  sx={{
                    position: 'absolute',
                    bottom: 10,
                    right: 10,
                    background: 'primary.main',
                    color: 'white',
                    '&:hover': { background: 'primary.dark' }
                  }}
                >
                  <CameraIcon />
                  <input
                    type="file"
                    hidden
                    accept="image/*"
                    onChange={handleImageChange}
                  />
                </IconButton>
              </Box>

              {/* IMAGE UPLOAD */}
              {profileImage && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Selected: {profileImage.name}
                  </Typography>
                  <Button
                    variant="contained"
                    fullWidth
                    disabled={uploading}
                    onClick={handleUploadImage}
                    startIcon={uploading ? <CircularProgress size={20} /> : <CameraIcon />}
                  >
                    {uploading ? 'Uploading...' : 'Upload Image'}
                  </Button>
                </Box>
              )}

              {/* USER INFO */}
              <Typography variant="h5" fontWeight="bold" gutterBottom>
                {user.first_name} {user.last_name}
              </Typography>
              
              <Typography variant="body1" color="text.secondary" gutterBottom>
                {user.email}
              </Typography>
              
              <Chip 
                label={user.role}
                color={
                  user.role === 'ADMINISTRATOR' ? 'error' :
                  user.role === 'MODERATOR' ? 'warning' : 'success'
                }
                sx={{ mb: 3 }}
              />

              <Divider sx={{ my: 3 }} />

              {/* ACCOUNT INFO */}
              <Box textAlign="left">
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Account Created
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {new Date(user.created_at).toLocaleDateString()}
                </Typography>
                
                <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  Last Updated
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {user.updated_at ? new Date(user.updated_at).toLocaleDateString() : 'Never'}
                </Typography>
                
                <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  Status
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {user.is_blocked ? (
                    <Chip icon={<ErrorIcon />} label="BLOCKED" color="error" size="small" />
                  ) : (
                    <Chip icon={<VerifiedIcon />} label="ACTIVE" color="success" size="small" />
                  )}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* RIGHT COLUMN - EDIT FORM */}
        <Grid item xs={12} md={8}>
          <Card sx={{ borderRadius: 3, boxShadow: 2 }}>
            <CardContent sx={{ p: 4 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
                <Typography variant="h4" fontWeight="bold">
                  Personal Information
                </Typography>
                
                {!isEditing ? (
                  <Button
                    variant="contained"
                    startIcon={<EditIcon />}
                    onClick={() => setIsEditing(true)}
                  >
                    Edit Profile
                  </Button>
                ) : (
                  <Box display="flex" gap={2}>
                    <Button
                      variant="outlined"
                      startIcon={<CancelIcon />}
                      onClick={handleCancel}
                      disabled={loading}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
                      onClick={handleSave}
                      disabled={loading || !hasChanges}
                    >
                      {loading ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </Box>
                )}
              </Box>

              <Divider sx={{ mb: 4 }} />

              <Grid container spacing={3}>
                {/* FIRST NAME */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="First Name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    variant="outlined"
                    required
                    disabled={!isEditing || loading}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <PersonIcon color="action" />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>

                {/* LAST NAME */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Last Name"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleChange}
                    variant="outlined"
                    required
                    disabled={!isEditing || loading}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <PersonIcon color="action" />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>

                {/* EMAIL (read-only) */}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email Address"
                    name="email"
                    value={formData.email}
                    variant="outlined"
                    disabled
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <EmailIcon color="action" />
                        </InputAdornment>
                      ),
                    }}
                    helperText="Email cannot be changed"
                  />
                </Grid>

                {/* DATE OF BIRTH */}
                <Grid item xs={12} sm={6}>
                  <LocalizationProvider dateAdapter={AdapterDateFns}>
                    <DatePicker
                      label="Date of Birth"
                      value={formData.date_of_birth}
                      onChange={handleDateChange}
                      disableFuture
                      disabled={!isEditing || loading}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          fullWidth
                          required
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
                </Grid>

                {/* GENDER */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    select
                    label="Gender"
                    name="gender"
                    value={formData.gender}
                    onChange={handleChange}
                    variant="outlined"
                    disabled={!isEditing || loading}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <GenderIcon color="action" />
                        </InputAdornment>
                      ),
                    }}
                  >
                    <MenuItem value=""><em>Select Gender</em></MenuItem>
                    <MenuItem value="M">Male</MenuItem>
                    <MenuItem value="F">Female</MenuItem>
                    <MenuItem value="O">Other</MenuItem>
                    <MenuItem value="N">Prefer not to say</MenuItem>
                  </TextField>
                </Grid>

                {/* COUNTRY */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Country"
                    name="country"
                    value={formData.country}
                    onChange={handleChange}
                    variant="outlined"
                    disabled={!isEditing || loading}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <CountryIcon color="action" />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>

                {/* STREET */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Street"
                    name="street"
                    value={formData.street}
                    onChange={handleChange}
                    variant="outlined"
                    disabled={!isEditing || loading}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <StreetIcon color="action" />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>

                {/* NUMBER */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Street Number"
                    name="number"
                    value={formData.number}
                    onChange={handleChange}
                    variant="outlined"
                    disabled={!isEditing || loading}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <NumberIcon color="action" />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
              </Grid>

              {/* EDITING NOTES */}
              {isEditing && (
                <Alert severity="info" sx={{ mt: 4, borderRadius: 2 }}>
                  <Typography variant="body2">
                    <strong>Note:</strong> All changes will be saved to the database immediately. 
                    Email address cannot be changed. Date of birth must be at least 13 years ago.
                  </Typography>
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/*  */}
    </Container>
  )
}

export default Profile