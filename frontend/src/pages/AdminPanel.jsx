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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  Tooltip,
  Badge,
  Divider,
  useTheme,
  useMediaQuery,
} from '@mui/material'
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  Block as BlockIcon,
  LockOpen as UnblockIcon,
  AdminPanelSettings as AdminIcon,
  Person as PersonIcon,
  BarChart as StatsIcon,
  Refresh as RefreshIcon,
  Email as EmailIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  PersonAdd as PersonAddIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { userAPI, quizAPI } from '../services/api'
import websocketService from '../services/websocket'
import { toast } from 'react-hot-toast'

const AdminPanel = () => {
  const { user, isAdmin } = useAuth()
  const navigate = useNavigate()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  
  // State-ovi
  const [users, setUsers] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Pagination
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)
  const [totalUsers, setTotalUsers] = useState(0)
  
  // Filteri
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  
// Quiz moderation
  const [pendingQuizzes, setPendingQuizzes] = useState([])
  const [quizLoading, setQuizLoading] = useState(false)
  const [quizError, setQuizError] = useState('')
  const [rejectDialog, setRejectDialog] = useState(false)
  const [selectedQuiz, setSelectedQuiz] = useState(null)
  const [rejectionReason, setRejectionReason] = useState('')
  const [quizActionLoading, setQuizActionLoading] = useState(false)

  // Dialogs
  const [changeRoleDialog, setChangeRoleDialog] = useState(false)
  const [blockDialog, setBlockDialog] = useState(false)
  const [deleteDialog, setDeleteDialog] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [newRole, setNewRole] = useState('')
  const [blockHours, setBlockHours] = useState(24)

  // Proveri da li je admin
  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    
    if (!isAdmin()) {
      toast.error('Access denied. Admin privileges required.')
      navigate('/dashboard')
      return
    }
    
    console.log(' AdminPanel loaded for:', user.email)
    fetchData()
  }, [user, isAdmin, navigate, page, rowsPerPage, search, roleFilter, statusFilter])

  useEffect(() => {
    websocketService.connect()
    const handleNewQuiz = (payload) => {
      if (payload?.status === 'PENDING') {
        setPendingQuizzes((prev) => {
          const exists = prev.some((quiz) => quiz.id === payload.id)
          return exists ? prev : [payload, ...prev]
        })
      }
    }
    const handleQuizDecision = (payload) => {
      if (payload?.id) {
        setPendingQuizzes((prev) => prev.filter((quiz) => quiz.id !== payload.id))
      }
    }
    websocketService.on('new_quiz_pending', handleNewQuiz)
    websocketService.on('quiz_approved', handleQuizDecision)
    websocketService.on('quiz_rejected', handleQuizDecision)
    return () => {
      websocketService.off('new_quiz_pending', handleNewQuiz)
      websocketService.off('quiz_approved', handleQuizDecision)
      websocketService.off('quiz_rejected', handleQuizDecision)
    }
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError('')
      
      // Fetch users sa paginacijom i filterima
      const usersResponse = await userAPI.getAllUsers(
        page + 1, 
        rowsPerPage, 
        search,
        roleFilter
      )
      
      setUsers(usersResponse.data.users)
      setTotalUsers(usersResponse.data.total)
      
      // Fetch statistics
      const statsResponse = await userAPI.getUserStats()
      setStats(statsResponse.data)

      await fetchPendingQuizzes()
      
    } catch (err) {
      console.error(' AdminPanel error:', err)
      setError(err.response?.data?.error || 'Failed to load admin data')
      toast.error('Failed to load admin data')
    } finally {
      setLoading(false)
    }
  }

   const fetchPendingQuizzes = async () => {
    try {
      setQuizLoading(true)
      setQuizError('')
      const response = await quizAPI.getQuizzes('PENDING')
      setPendingQuizzes(response.data.quizzes || [])
    } catch (err) {
      console.error(' Failed to load pending quizzes:', err)
      setQuizError(err.response?.data?.error || 'Failed to load pending quizzes')
    } finally {
      setQuizLoading(false)
    }
  }

  const handleApproveQuiz = async (quizId) => {
    try {
      setQuizActionLoading(true)
      await quizAPI.approveQuiz(quizId)
      toast.success('Quiz approved')
      setPendingQuizzes((prev) => prev.filter((quiz) => quiz.id !== quizId))
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to approve quiz')
    } finally {
      setQuizActionLoading(false)
    }
  }

  const handleOpenReject = (quiz) => {
    setSelectedQuiz(quiz)
    setRejectionReason('')
    setRejectDialog(true)
  }

  const handleRejectQuiz = async () => {
    if (!selectedQuiz) return
    if (!rejectionReason.trim()) {
      toast.error('Rejection reason is required')
      return
    }
    try {
      setQuizActionLoading(true)
      await quizAPI.rejectQuiz(selectedQuiz.id, rejectionReason)
      toast.success('Quiz rejected')
      setPendingQuizzes((prev) => prev.filter((quiz) => quiz.id !== selectedQuiz.id))
      setRejectDialog(false)
      setSelectedQuiz(null)
      setRejectionReason('')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to reject quiz')
    } finally {
      setQuizActionLoading(false)
    }
  }


  const handleChangeRole = async () => {
    if (!selectedUser || !newRole) return
    
    try {
      await userAPI.updateUserRole(selectedUser.id, newRole)
      
      toast.success(`Role changed to ${newRole}`, {
        icon: '👑',
        duration: 3000
      })
      
      // Refresh data
      fetchData()
      setChangeRoleDialog(false)
      setSelectedUser(null)
      setNewRole('')
      
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to change role')
    }
  }

  const handleBlockUser = async () => {
    if (!selectedUser) return
    
    try {
      await userAPI.blockUser(selectedUser.id, blockHours)
      
      toast.success(`User blocked for ${blockHours} hours`, {
        icon: '🔒',
        duration: 3000
      })
      
      fetchData()
      setBlockDialog(false)
      setSelectedUser(null)
      
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to block user')
    }
  }

  const handleUnblockUser = async (userId) => {
    try {
      await userAPI.unblockUser(userId)
      
      toast.success('User unblocked', {
        icon: '🔓',
        duration: 3000
      })
      
      fetchData()
      
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to unblock user')
    }
  }

  const handleDeleteUser = async () => {
    if (!selectedUser) return
    
    if (selectedUser.id === user.id) {
      toast.error('You cannot delete your own account')
      return
    }
    
    try {
      await userAPI.deleteUser(selectedUser.id)
      
      toast.success('User deleted successfully', {
        icon: '🗑️',
        duration: 3000
      })
      
      fetchData()
      setDeleteDialog(false)
      setSelectedUser(null)
      
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to delete user')
    }
  }

  const handleRefresh = () => {
    fetchData()
    toast.success('Data refreshed', {
      icon: '🔄',
      duration: 2000
    })
  }

  const handlePageChange = (event, newPage) => {
    setPage(newPage)
  }

  const handleRowsPerPageChange = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const getRoleColor = (role) => {
    switch (role) {
      case 'ADMINISTRATOR': return 'error'
      case 'MODERATOR': return 'warning'
      case 'IGRAČ': return 'success'
      default: return 'default'
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString()
  }

  if (!user || !isAdmin()) {
    return null
  }

  if (loading && !stats) {
    return (
      <Container maxWidth="xl" sx={{ py: 8 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <CircularProgress size={60} />
        </Box>
      </Container>
    )
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* HEADER */}
      <Paper 
        sx={{ 
          p: 4, 
          mb: 4, 
          background: 'linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%)',
          color: 'white',
          borderRadius: 3,
          boxShadow: 3
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={3}>
          <Box display="flex" alignItems="center" gap={3}>
            <AdminIcon sx={{ fontSize: 50 }} />
            <Box>
              <Typography variant="h3" fontWeight="bold" gutterBottom>
                 Administrator Panel
              </Typography>
              <Typography variant="h6" sx={{ opacity: 0.9 }}>
                Full control over platform users and content
              </Typography>
            </Box>
          </Box>
          
          <Box display="flex" gap={2}>
            <Button
              variant="contained"
              color="secondary"
              onClick={handleRefresh}
              startIcon={<RefreshIcon />}
              sx={{ 
                background: 'rgba(255,255,255,0.9)',
                color: '#d32f2f',
                '&:hover': { background: 'white' }
              }}
            >
              Refresh
            </Button>
            
            <Button
              variant="outlined"
              sx={{ 
                color: 'white', 
                borderColor: 'white',
                '&:hover': { borderColor: 'white', background: 'rgba(255,255,255,0.1)' }
              }}
              onClick={() => navigate('/dashboard')}
            >
              Back to Dashboard
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
            <Button color="inherit" size="small" onClick={fetchData}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      )}

      {/* STATISTICS */}
      {stats && (
        <Paper sx={{ p: 4, mb: 6, borderRadius: 3, boxShadow: 2 }}>
          <Box display="flex" alignItems="center" gap={2} mb={4}>
            <StatsIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Typography variant="h4" fontWeight="bold">
              Platform Statistics
            </Typography>
          </Box>
          
          <Divider sx={{ mb: 4 }} />
          
          <Grid container spacing={3}>
            <Grid item xs={6} sm={4} md={2}>
              <Card sx={{ borderRadius: 2, height: '100%' }}>
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
              <Card sx={{ borderRadius: 2, height: '100%' }}>
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
              <Card sx={{ borderRadius: 2, height: '100%' }}>
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
              <Card sx={{ borderRadius: 2, height: '100%' }}>
                <CardContent sx={{ textAlign: 'center', p: 3 }}>
                  <Typography variant="h3" fontWeight="bold" color="error.main">
                    {stats.admins}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Administrators
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={6} sm={4} md={2}>
              <Card sx={{ borderRadius: 2, height: '100%' }}>
                <CardContent sx={{ textAlign: 'center', p: 3 }}>
                  <Typography variant="h3" fontWeight="bold" color="info.main">
                    {stats.blocked_users}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Blocked Users
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={6} sm={4} md={2}>
              <Card sx={{ borderRadius: 2, height: '100%' }}>
                <CardContent sx={{ textAlign: 'center', p: 3 }}>
                  <Typography variant="h3" fontWeight="bold" color="secondary.main">
                    {stats.new_users_last_week}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    New (7 days)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* QUIZ MODERATION */}
      <Paper sx={{ p: 4, mb: 6, borderRadius: 3, boxShadow: 2 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" gap={2} mb={3} flexWrap="wrap">
          <Box display="flex" alignItems="center" gap={2}>
            <CheckIcon sx={{ fontSize: 36, color: 'success.main' }} />
            <Typography variant="h4" fontWeight="bold">
              Pending Quizzes
            </Typography>
          </Box>
          <Button variant="outlined" onClick={fetchPendingQuizzes} startIcon={<RefreshIcon />}>
            Refresh
          </Button>
        </Box>

        {quizError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {quizError}
          </Alert>
        )}

        {quizLoading ? (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        ) : pendingQuizzes.length === 0 ? (
          <Alert severity="info">No quizzes awaiting approval.</Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Quiz</TableCell>
                  <TableCell>Author</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Questions</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {pendingQuizzes.map((quiz) => (
                  <TableRow key={quiz.id}>
                    <TableCell>
                      <Typography fontWeight="bold">{quiz.title}</Typography>
                    </TableCell>
                    <TableCell>{quiz.author_name}</TableCell>
                    <TableCell>{quiz.duration_seconds}s</TableCell>
                    <TableCell>{quiz.question_count}</TableCell>
                    <TableCell align="right">
                      <Box display="flex" justifyContent="flex-end" gap={1}>
                        <Button
                          variant="contained"
                          color="success"
                          size="small"
                          startIcon={<CheckIcon />}
                          onClick={() => handleApproveQuiz(quiz.id)}
                          disabled={quizActionLoading}
                        >
                          Approve
                        </Button>
                        <Button
                          variant="outlined"
                          color="error"
                          size="small"
                          startIcon={<ErrorIcon />}
                          onClick={() => handleOpenReject(quiz)}
                          disabled={quizActionLoading}
                        >
                          Reject
                        </Button>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>


      {/* USER MANAGEMENT */}
      <Paper sx={{ p: 4, borderRadius: 3, boxShadow: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={4} flexWrap="wrap" gap={3}>
          <Typography variant="h4" fontWeight="bold">
             User Management
          </Typography>
          
          <Box display="flex" gap={2} flexWrap="wrap">
            {/* Search */}
            <TextField
              size="small"
              placeholder="Search users..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'action.active' }} />,
              }}
            />
            
            {/* Role Filter */}
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Filter by Role</InputLabel>
              <Select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                label="Filter by Role"
              >
                <MenuItem value="">All Roles</MenuItem>
                <MenuItem value="IGRAČ">Player</MenuItem>
                <MenuItem value="MODERATOR">Moderator</MenuItem>
                <MenuItem value="ADMINISTRATOR">Administrator</MenuItem>
              </Select>
            </FormControl>
            
            {/* Status Filter */}
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Filter by Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Filter by Status"
              >
                <MenuItem value="">All Status</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="blocked">Blocked</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>

        <Divider sx={{ mb: 4 }} />

        {/* USERS TABLE */}
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: 'action.hover' }}>
                <TableCell><strong>ID</strong></TableCell>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Email</strong></TableCell>
                <TableCell><strong>Role</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>Created</strong></TableCell>
                <TableCell><strong>Last Login</strong></TableCell>
                <TableCell><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      No users found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                users.map((userItem) => (
                  <TableRow 
                    key={userItem.id}
                    hover
                    sx={{ 
                      bgcolor: userItem.is_blocked ? 'rgba(244, 67, 54, 0.05)' : 'inherit',
                      opacity: userItem.is_blocked ? 0.7 : 1
                    }}
                  >
                    <TableCell>{userItem.id}</TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {userItem.profile_image && (
                          <img 
                            src={`${import.meta.env.VITE_API_URL}/uploads/profile-pictures/${userItem.profile_image}`}
                            alt={userItem.first_name}
                            style={{ 
                              width: 30, 
                              height: 30, 
                              borderRadius: '50%',
                              objectFit: 'cover'
                            }}
                          />
                        )}
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {userItem.first_name} {userItem.last_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {userItem.gender || 'Not specified'}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>{userItem.email}</TableCell>
                    <TableCell>
                      <Chip 
                        label={userItem.role}
                        color={getRoleColor(userItem.role)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {userItem.is_blocked ? (
                        <Chip 
                          icon={<BlockIcon />}
                          label="BLOCKED"
                          color="error"
                          size="small"
                        />
                      ) : (
                        <Chip 
                          icon={<CheckIcon />}
                          label="ACTIVE"
                          color="success"
                          size="small"
                        />
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(userItem.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {userItem.last_login ? formatDate(userItem.last_login) : 'Never'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={1}>
                        {/* Change Role */}
                        <Tooltip title="Change Role">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => {
                              setSelectedUser(userItem)
                              setNewRole(userItem.role)
                              setChangeRoleDialog(true)
                            }}
                            disabled={userItem.id === user.id}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        
                        {/* Block/Unblock */}
                        {userItem.is_blocked ? (
                          <Tooltip title="Unblock User">
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => handleUnblockUser(userItem.id)}
                              disabled={userItem.id === user.id}
                            >
                              <UnblockIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        ) : (
                          <Tooltip title="Block User">
                            <IconButton
                              size="small"
                              color="warning"
                              onClick={() => {
                                setSelectedUser(userItem)
                                setBlockDialog(true)
                              }}
                              disabled={userItem.id === user.id}
                            >
                              <BlockIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        
                        {/* Delete */}
                        <Tooltip title="Delete User">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => {
                              setSelectedUser(userItem)
                              setDeleteDialog(true)
                            }}
                            disabled={userItem.id === user.id}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* PAGINATION */}
        <TablePagination
          component="div"
          count={totalUsers}
          page={page}
          onPageChange={handlePageChange}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleRowsPerPageChange}
          rowsPerPageOptions={[5, 10, 25, 50]}
          sx={{ mt: 2 }}
        />
      </Paper>

      {/* CHANGE ROLE DIALOG */}
      <Dialog open={changeRoleDialog} onClose={() => setChangeRoleDialog(false)}>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <EditIcon color="primary" />
            Change User Role
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedUser && (
            <>
              <Typography variant="body1" gutterBottom>
                User: <strong>{selectedUser.first_name} {selectedUser.last_name}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Email: {selectedUser.email}
              </Typography>
              
              <FormControl fullWidth sx={{ mt: 3 }}>
                <InputLabel>New Role</InputLabel>
                <Select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  label="New Role"
                >
                  <MenuItem value="IGRAČ">IGRAČ (Player)</MenuItem>
                  <MenuItem value="MODERATOR">MODERATOR</MenuItem>
                  <MenuItem value="ADMINISTRATOR">ADMINISTRATOR</MenuItem>
                </Select>
              </FormControl>
              
              <Alert severity="info" sx={{ mt: 3 }}>
                <Typography variant="body2">
                  • User will receive an email notification about role change
                  <br/>
                  • Only administrators can assign MODERATOR and ADMINISTRATOR roles
                  <br/>
                  • Administrators have full control over the platform
                </Typography>
              </Alert>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChangeRoleDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleChangeRole}
            disabled={!newRole || newRole === selectedUser?.role}
          >
            Change Role
          </Button>
        </DialogActions>
      </Dialog>

      {/* BLOCK USER DIALOG */}
      <Dialog open={blockDialog} onClose={() => setBlockDialog(false)}>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <BlockIcon color="warning" />
            Block User
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedUser && (
            <>
              <Typography variant="body1" gutterBottom>
                User: <strong>{selectedUser.first_name} {selectedUser.last_name}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Email: {selectedUser.email}
              </Typography>
              
              <TextField
                fullWidth
                type="number"
                label="Block Duration (hours)"
                value={blockHours}
                onChange={(e) => setBlockHours(e.target.value)}
                sx={{ mt: 3 }}
                InputProps={{ inputProps: { min: 1, max: 720 } }}
                helperText="1-720 hours (1-30 days)"
              />
              
              <Alert severity="warning" sx={{ mt: 3 }}>
                <Typography variant="body2">
                  • User will not be able to login during this period
                  <br/>
                  • All active sessions will be terminated
                  <br/>
                  • User can be unblocked anytime by an administrator
                </Typography>
              </Alert>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBlockDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            color="warning"
            onClick={handleBlockUser}
          >
            Block User
          </Button>
        </DialogActions>
      </Dialog>

      {/* DELETE USER DIALOG */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)}>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <DeleteIcon color="error" />
            Delete User
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedUser && (
            <>
              <Alert severity="error" sx={{ mb: 3 }}>
                <Typography variant="subtitle2" fontWeight="bold">
                   WARNING: This action cannot be undone!
                </Typography>
              </Alert>
              
              <Typography variant="body1" gutterBottom>
                Are you sure you want to delete this user?
              </Typography>
              
              <Typography variant="body2" gutterBottom>
                User: <strong>{selectedUser.first_name} {selectedUser.last_name}</strong>
              </Typography>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Email: {selectedUser.email}
              </Typography>
              
              <Typography variant="body2" color="text.secondary">
                Role: {selectedUser.role}
              </Typography>
              
              <Alert severity="info" sx={{ mt: 3 }}>
                <Typography variant="body2">
                  • All user data will be permanently deleted
                  <br/>
                  • Profile image will be removed from server
                  <br/>
                  • Quiz results and history will be lost
                  <br/>
                  • This action is irreversible
                </Typography>
              </Alert>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            color="error"
            onClick={handleDeleteUser}
            disabled={selectedUser?.id === user?.id}
          >
            Delete User
          </Button>
        </DialogActions>
      </Dialog>

      {/* REJECT QUIZ DIALOG */}
      <Dialog open={rejectDialog} onClose={() => setRejectDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <WarningIcon color="error" />
            Reject Quiz
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Provide a reason for rejection. The quiz will be sent back to the moderator for edits.
          </Typography>
          <TextField
            fullWidth
            multiline
            minRows={3}
            label="Rejection reason"
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleRejectQuiz}
            disabled={quizActionLoading}
          >
            Reject Quiz
          </Button>
        </DialogActions>
      </Dialog>

      {/* FOOTER */}
      <Box sx={{ mt: 6, pt: 4, borderTop: 1, borderColor: 'divider' }}>
        <Typography variant="body2" color="textSecondary" align="center">
          Admin Panel • Quiz Platform • Distributed Systems 2025/2026
        </Typography>
        <Typography variant="caption" color="textSecondary" align="center" display="block" sx={{ mt: 1 }}>
          Logged in as: {user?.email} • Total Users: {totalUsers} • Last Updated: {new Date().toLocaleTimeString()}
        </Typography>
      </Box>
    </Container>
  )
}

export default AdminPanel