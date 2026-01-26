import { authAPI } from './api.js';

//  TOKEN HELPER FUNKCIJE
export const tokenHelper = {
  saveTokens: (accessToken, refreshToken, user) => {
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    }
  },
  
  getAccessToken: () => localStorage.getItem('access_token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  getUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
  
  clearTokens: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
  
  isValidToken: (token) => {
    if (!token) return false;
    
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return false;
      
      const payload = JSON.parse(atob(parts[1]));
      const exp = payload.exp * 1000;
      const isValid = Date.now() < exp;
      
      console.log(` Token expires: ${new Date(exp).toLocaleString()}, valid: ${isValid}`);
      return isValid;
      
    } catch (error) {
      console.error(' Error validating token:', error);
      return false;
    }
  }
};

//  SERVIS ZA AUTENTIFIKACIJU 
export const authService = {
  //  VALIDACIJA TOKENA
  validateToken: async (token) => {
    try {
      if (!token) return false;
      return tokenHelper.isValidToken(token);
    } catch (error) {
      console.error(' Token validation error:', error);
      return false;
    }
  },
  
  //  LOGIN 
  login: async (email, password) => {
    try {
      console.log(' Login attempt:', email);
      
      const response = await authAPI.login(email, password);
      const data = response.data;
      
      console.log(' Login API response:', data);
      
      // Provjeri različite formate responsa
      if (data.access_token) {
        // Sačuvaj tokene
        tokenHelper.saveTokens(data.access_token, data.refresh_token, data.user);
        
        console.log(' Login successful, tokens saved');
        return {
          success: true,
          user: data.user,
          access_token: data.access_token,
          message: data.message || 'Login successful',
          blocked: data.blocked || false,
          blocked_until: data.blocked_until,
          attempts_left: data.attempts_left
        };
      } 
      // Alternativni format
      else if (data.user && data.token) {
        tokenHelper.saveTokens(data.token, data.refresh_token, data.user);
        
        return {
          success: true,
          user: data.user,
          access_token: data.token,
          message: data.message || 'Login successful'
        };
      }
      // Ako je blokiran
      else if (data.blocked) {
        return {
          success: false,
          blocked: true,
          blocked_until: data.blocked_until,
          remaining_seconds: data.remaining_seconds,
          message: data.message || 'Account blocked'
        };
      }
      // Ako ima pokušaje
      else if (data.attempts_left !== undefined) {
        return {
          success: false,
          attempts_left: data.attempts_left,
          error: data.message || data.error || 'Invalid credentials'
        };
      }
      // Neuspješan login
      else {
        return {
          success: false,
          error: data.message || data.error || 'Login failed'
        };
      }
      
    } catch (error) {
      console.error(' Login API error:', error);
      
      const errorData = error.response?.data || {};
      return {
        success: false,
        error: errorData.message || errorData.error || error.message || 'Login failed',
        blocked: errorData.blocked,
        blocked_until: errorData.blocked_until,
        attempts_left: errorData.attempts_left,
        status: error.response?.status
      };
    }
  },
  
  //  REGISTRACIJA
  register: async (userData) => {
    try {
      console.log(' Registration attempt:', userData.email);
      
      const response = await authAPI.register(userData);
      const data = response.data;
      
      console.log(' Registration response:', data);
      
      if (data.access_token && data.user) {
        tokenHelper.saveTokens(data.access_token, data.refresh_token, data.user);
        
        return {
          success: true,
          user: data.user,
          access_token: data.access_token
        };
      } else {
        return {
          success: false,
          error: data.message || data.error || 'Registration failed'
        };
      }
      
    } catch (error) {
      console.error(' Registration API error:', error);
      
      const errorData = error.response?.data || {};
      return {
        success: false,
        error: errorData.message || errorData.error || error.message || 'Registration failed'
      };
    }
  },
  
  //  LOGOUT
  logout: async () => {
    try {
      console.log('🚪 Logout attempt');
      
      const response = await authAPI.logout();
      
      // Uvek očisti tokene
      tokenHelper.clearTokens();
      
      return {
        success: true,
        data: response.data
      };
      
    } catch (error) {
      console.error(' Logout error:', error);
      
      // U svakom slučaju očisti tokene
      tokenHelper.clearTokens();
      
      return {
        success: false,
        error: error.message || 'Logout failed'
      };
    }
  },
  
  //  DOBAVI TRENUTNOG KORISNIKA
  getCurrentUser: () => tokenHelper.getUser(),
  
  //  PROVJERA AUTENTIFIKACIJE
  isAuthenticated: () => {
    const token = tokenHelper.getAccessToken();
    return token && tokenHelper.isValidToken(token);
  },
  
  //  REFRESH TOKEN (ako postoji endpoint)
  refreshToken: async () => {
    try {
      const refreshToken = tokenHelper.getRefreshToken();
      if (!refreshToken) throw new Error('No refresh token');
      
      const response = await authAPI.refreshToken(refreshToken);
      const data = response.data;
      
      if (data.access_token) {
        const user = tokenHelper.getUser();
        tokenHelper.saveTokens(data.access_token, data.refresh_token, user);
        return { success: true, access_token: data.access_token };
      }
      
      return { success: false, error: data.message };
      
    } catch (error) {
      console.error(' Refresh token error:', error);
      return { success: false, error: error.message };
    }
  }
};

export default authService;
