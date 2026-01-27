import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Container, CssBaseline } from '@mui/material'
import { Toaster } from 'react-hot-toast'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { AuthProvider } from './context/AuthContext'

// Komponente
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import AdminPanel from './pages/AdminPanel'
import CreateQuiz from './pages/CreateQuiz'
import QuizList from './pages/QuizList'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'

// Tema
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#9c27b0',
      light: '#ba68c8',
      dark: '#7b1fa2',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
    },
    h2: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
})

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        {/* Toast Notifikacije */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
              borderRadius: '8px',
              fontSize: '14px',
            },
          }}
        />
        
        <Routes>
          {/* Public rute bez Navbar-a */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Sve ostale rute sa Navbar-om */}
          <Route path="/*" element={<MainLayout />} />
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  )
}

// Glavni layout sa Navbar-om
function MainLayout() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <Container maxWidth="xl" sx={{ py: 4, flex: 1 }}>
        <Routes>
          {/* Redirekt sa root na dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* Protected rute */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/profile" element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } />
          
          <Route path="/admin" element={
            <ProtectedRoute requiredRole="ADMINISTRATOR">
              <AdminPanel />
            </ProtectedRoute>
          } />

                    <Route path="/quizzes" element={
            <ProtectedRoute>
              <QuizList />
            </ProtectedRoute>
          } />

          <Route path="/create-quiz" element={
            <ProtectedRoute requiredRole="MODERATOR" allowAdmin={false}>
              <CreateQuiz />
            </ProtectedRoute>
          } />
          
          {/* 404 ruta */}
          <Route path="*" element={
            <ProtectedRoute>
              <Navigate to="/dashboard" replace />
            </ProtectedRoute>
          } />
        </Routes>
      </Container>
    </div>
  )
}

export default App