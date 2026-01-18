import axios from 'axios';

// Base URL 
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

console.log('🔗 API URL configured:', API_URL);

// Kreiranje axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 30000, // 30 sekundi timeout
});

//  Request interceptor - dodaje token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

//  Response interceptor - hvata greške
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    console.error('API Error:', error.response?.status, error.response?.data);
    
    // Ako je 401 (Unauthorized)
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      
      // Redirect na login ako nismo već tu
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
      }
    }
    
    // Ako je 429 (Too Many Requests - blokiran zbog login pokušaja)
    if (error.response?.status === 429) {
      const blockedUntil = error.response?.data?.blocked_until;
      const remaining = error.response?.data?.remaining_seconds;
      console.warn(` Account blocked until: ${blockedUntil}, remaining: ${remaining}s`);
    }
    
    return Promise.reject(error);
  }
);

// AUTH API 
export const authAPI = {
  //  REGISTRACIJA 
  register: (userData) => api.post('/api/auth/register', userData),
  
  //  LOGIN - vraća access_token i refresh_token
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  
  //  LOGOUT
  logout: () => api.post('/api/auth/logout'),
  
  //  REFRESH TOKEN
  refreshToken: (refreshToken) => api.post('/api/auth/refresh', { refresh_token: refreshToken }),
  
  //  VALIDACIJA TOKENA
  validateToken: () => api.get('/api/auth/validate'),
  
  //  PROFIL KORISNIKA
  getProfile: () => api.get('/api/profile')
};

//  USER API
export const userAPI = {
  //  SVI KORISNICI (samo admin) - sa paginacijom
  getAllUsers: (page = 1, perPage = 20, search = '') => 
    api.get(`/api/users?page=${page}&per_page=${perPage}&search=${search}`),
  
  //  PROMENA ULOGE (samo admin)
  updateUserRole: (userId, role) => api.put(`/api/users/${userId}/role`, { role }),
  
  //  BRIŠI KORISNIKA (samo admin)
  deleteUser: (userId) => api.delete(`/api/users/${userId}`),
  
  //  BLOKIRAJ KORISNIKA (samo admin)
  blockUser: (userId, hours = 24) => api.put(`/api/users/${userId}/block`, { block: true, hours }),
  
  //  ODBLOKIRAJ KORISNIKA (samo admin)
  unblockUser: (userId) => api.put(`/api/users/${userId}/block`, { block: false }),
  
  //  STATISTIKA KORISNIKA (samo admin)
  getUserStats: () => api.get('/api/users/stats'),
  
  //  UPDATE PROFILA
  updateProfile: (userData) => api.put('/api/profile', userData),
  
  //  UPLOAD PROFILNE SLIKE
  uploadProfileImage: (formData) => 
    api.post('/api/profile/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
};

//  DASHBOARD API
export const dashboardAPI = {
  getStats: () => api.get('/api/users/stats'), // Koristi postojeći endpoint
  getQuizzes: () => api.get('/quizzes') 
};

//  TOKEN HELPER FUNKCIJE 
export const tokenHelper = {
  //  ČUVANJE TOKENA (kao što backend vraća)
  saveTokens: (accessToken, refreshToken, user) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('user', JSON.stringify(user));
  },
  
  //  DOBAVLJANJE TOKENA
  getAccessToken: () => localStorage.getItem('access_token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  getUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
  
  //  ČIŠĆENJE TOKENA
  clearTokens: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
  
  //  PROVERA VALIDNOSTI TOKENA
  isValidToken: (token) => {
    if (!token) return false;
    
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return false;
      
      // Proveri da li je token istekao
      const payload = JSON.parse(atob(parts[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      return Date.now() < exp;
    } catch (error) {
      console.error('Error validating token:', error);
      return false;
    }
  },
  
  //  DEKODIRANJE TOKENA (za dobijanje user_id i role)
  decodeToken: (token) => {
    try {
      if (!token || typeof token !== 'string') return null;
      
      const parts = token.split('.');
      if (parts.length !== 3) return null;
      
      const base64Url = parts[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Error decoding token:', error);
      return null;
    }
  },
  
  //  DOBAVI PAYLOAD IZ TRENUTNOG TOKENA
  getTokenPayload: () => {
    const token = localStorage.getItem('access_token');
    return tokenHelper.decodeToken(token);
  },
  
  //  PROVERI DA LI JE KORISNIK ADMIN
  isAdmin: () => {
    const user = tokenHelper.getUser();
    return user && user.role === 'ADMINISTRATOR';
  },
  
  //  PROVERI DA LI JE KORISNIK MODERATOR
  isModerator: () => {
    const user = tokenHelper.getUser();
    return user && (user.role === 'MODERATOR' || user.role === 'ADMINISTRATOR');
  },
  
  //  PROVERI DA LI JE KORISNIK IGRAČ
  isPlayer: () => {
    const user = tokenHelper.getUser();
    return user && user.role === 'IGRAČ';
  }
};

export default api;