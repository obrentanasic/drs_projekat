import React, { createContext, useState, useContext, useEffect } from 'react'
import { toast } from 'react-hot-toast'
import { authService, tokenHelper } from '../services/auth'
import { userAPI } from '../services/api'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const initializeAuth = async () => {
      console.log('🔄 AuthContext: Checking authentication...')
      
      try {
        const token = localStorage.getItem('access_token')
        const userStr = localStorage.getItem('user')
        
        if (token && userStr) {
          console.log(' Found token and user in localStorage')
          
          // Validacija tokena
          const isValid = await authService.validateToken(token)
          
          if (isValid) {
            const userData = JSON.parse(userStr)
            setUser(userData)
            setIsAuthenticated(true)
            console.log(' User authenticated from localStorage:', userData.email)
          } else {
            console.log(' Token invalid or expired')
            authService.logout()
          }
        } else {
          console.log(' No auth data found')
        }
      } catch (error) {
        console.error(' Auth initialization error:', error)
        authService.logout()
      } finally {
        setIsLoading(false)
        console.log(' AuthContext initialized, loading:', false)
      }
    }
    
    initializeAuth()
  }, [])

  const login = async (email, password) => {
    console.log('🔐 AuthContext login called for:', email)
    
    try {
      const result = await authService.login(email, password)
      console.log('📊 Login result from authService:', result)
      
      if (result.success && result.user) {
        // SINHRONO ažuriraj stanje
        setUser(result.user)
        setIsAuthenticated(true)
        
        // Postavi header za buduće API pozive
        if (userAPI.defaults && userAPI.defaults.headers) {
          userAPI.defaults.headers.common['Authorization'] = `Bearer ${result.access_token}`
        }
        
        toast.success(`Welcome back, ${result.user.first_name || result.user.email}!`, {
          duration: 3000,
          icon: '👋'
        })
        
        return { 
          success: true, 
          user: result.user,
          blocked: false 
        }
      } else {
        // Rukovanje errorima
        if (result.blocked) {
          toast.error(`Account blocked. Try again in ${result.remaining_seconds} seconds.`, {
            duration: 5000,
            icon: '⏰'
          })
          return { 
            success: false, 
            blocked: true,
            blocked_until: result.blocked_until,
            remaining_seconds: result.remaining_seconds
          }
        } else if (result.attempts_left !== undefined) {
          toast.error(`Invalid credentials. ${result.attempts_left} attempts remaining.`, {
            duration: 4000,
            icon: '⚠️'
          })
          return { 
            success: false, 
            attempts_left: result.attempts_left,
            error: result.error || 'Invalid credentials'
          }
        } else {
          toast.error(result.error || 'Login failed', {
            duration: 4000,
            icon: '❌'
          })
          return { success: false, error: result.error }
        }
      }
    } catch (error) {
      console.error(' AuthContext login error:', error)
      toast.error(error.message || 'An unexpected error occurred', {
        duration: 4000,
        icon: '❌'
      })
      return { success: false, error: error.message }
    }
  }

  const logout = async () => {
    console.log(' AuthContext logout called')
    
    try {
      await authService.logout()
      
      // Resetuj stanje
      setUser(null)
      setIsAuthenticated(false)
      
      // Očisti header
      if (userAPI.defaults && userAPI.defaults.headers) {
        delete userAPI.defaults.headers.common['Authorization']
      }
      
      toast.success('Logged out successfully', {
        duration: 3000,
        icon: '👋'
      })
      
      return { success: true }
    } catch (error) {
      console.error(' AuthContext logout error:', error)
      
      // U svakom slučaju resetuj stanje
      authService.logout()
      setUser(null)
      setIsAuthenticated(false)
      
      toast.success('Logged out', {
        duration: 3000,
        icon: '👋'
      })
      
      return { success: false, error: error.message }
    }
  }

  // ✅ REGISTER
  const register = async (userData) => {
    try {
      const result = await authService.register(userData)
      
      if (result.success && result.user) {
        setUser(result.user)
        setIsAuthenticated(true)
        
        if (userAPI.defaults && userAPI.defaults.headers) {
          userAPI.defaults.headers.common['Authorization'] = `Bearer ${result.access_token}`
        }
        
        toast.success(`Welcome ${result.user.first_name}! Registration successful.`, {
          duration: 4000,
          icon: '🎉'
        })
        
        return { success: true, user: result.user }
      } else {
        toast.error(result.error || 'Registration failed', {
          duration: 4000,
          icon: '❌'
        })
        return { success: false, error: result.error }
      }
    } catch (error) {
      toast.error(error.message || 'Registration failed', {
        duration: 4000,
        icon: '❌'
      })
      return { success: false, error: error.message }
    }
  }

  const updateProfile = async (userData) => {
    try {
      const response = await userAPI.updateProfile(userData)
      const updatedUser = response.data?.user || response.data
      
      // Ažuriraj lokalno
      localStorage.setItem('user', JSON.stringify(updatedUser))
      setUser(updatedUser)
      
      toast.success('Profile updated successfully!', {
        duration: 3000,
        icon: '✅'
      })
      
      return { success: true, user: updatedUser }
    } catch (error) {
      console.error(' Update profile error:', error)
      toast.error(error.response?.data?.error || 'Failed to update profile', {
        duration: 4000,
        icon: '❌'
      })
      throw error
    }
  }

  const checkAuth = () => {
    const token = localStorage.getItem('access_token')
    const userStr = localStorage.getItem('user')
    
    if (token && userStr) {
      const isValid = tokenHelper.isValidToken(token)
      if (isValid) {
        const userData = JSON.parse(userStr)
        setUser(userData)
        setIsAuthenticated(true)
        return true
      }
    }
    
    // Ako nije validan, logout
    logout()
    return false
  }

  const hasRole = (role) => {
    if (!user) return false
    if (user.role === 'ADMINISTRATOR') return true
    return user.role === role
  }

  const isAdmin = () => hasRole('ADMINISTRATOR')
  const isModerator = () => hasRole('MODERATOR') || isAdmin()
  const isPlayer = () => hasRole('IGRAČ') || isModerator()

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    register,
    updateProfile,
    checkAuth,
    hasRole,
    isAdmin,
    isModerator,
    isPlayer
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}