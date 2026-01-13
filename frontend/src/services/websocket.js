import { io } from 'socket.io-client'

class WebSocketService {
  constructor() {
    this.socket = null
    this.listeners = new Map()
    this.connected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
  }

  /**
   * Povezivanje na WebSocket server
   */
  connect() {
    try {
      const token = localStorage.getItem('access_token')
      
      if (!token) {
        console.warn('⚠️ No token available for WebSocket connection')
        return false
      }

      // Ako je već konektovan, ne konektuj ponovo
      if (this.socket?.connected) {
        console.log('✅ WebSocket already connected')
        return true
      }

      // Kreiraj novu konekciju
      const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:5000'
      
      this.socket = io(WS_URL, {
        query: { token },
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: 1000,
        timeout: 20000,
      })

      // Event handlers
      this.socket.on('connect', () => {
        console.log('✅ WebSocket connected, ID:', this.socket.id)
        this.connected = true
        this.reconnectAttempts = 0
        this.emitEvent('connected', { socketId: this.socket.id })
      })

      this.socket.on('disconnect', (reason) => {
        console.log('🔌 WebSocket disconnected:', reason)
        this.connected = false
        
        if (reason === 'io server disconnect') {
          // Server namerno diskonektovao, pokušaj ponovo
          setTimeout(() => this.connect(), 1000)
        }
      })

      this.socket.on('connect_error', (error) => {
        console.error('❌ WebSocket connection error:', error.message)
        this.connected = false
        this.reconnectAttempts++
        
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          console.error('💥 Max reconnection attempts reached')
        }
      })

      this.socket.on('reconnect', (attemptNumber) => {
        console.log(`🔄 WebSocket reconnected after ${attemptNumber} attempts`)
        this.connected = true
      })

      this.socket.on('reconnect_attempt', (attemptNumber) => {
        console.log(`🔄 WebSocket reconnection attempt ${attemptNumber}`)
      })

      this.socket.on('reconnect_error', (error) => {
        console.error('❌ WebSocket reconnection error:', error)
      })

      this.socket.on('reconnect_failed', () => {
        console.error('💥 WebSocket reconnection failed')
      })

      // Backend event-i
      this.socket.on('new_quiz_pending', (data) => {
        console.log('📝 New quiz pending approval:', data)
        this.emitEvent('new_quiz_pending', data)
      })

      this.socket.on('quiz_approved', (data) => {
        console.log('✅ Quiz approved:', data)
        this.emitEvent('quiz_approved', data)
      })

      this.socket.on('quiz_rejected', (data) => {
        console.log('❌ Quiz rejected:', data)
        this.emitEvent('quiz_rejected', data)
      })

      this.socket.on('admin_notification', (data) => {
        console.log('👑 Admin notification:', data)
        this.emitEvent('admin_notification', data)
      })

      this.socket.on('system_message', (data) => {
        console.log('📢 System message:', data)
        this.emitEvent('system_message', data)
      })

      this.socket.on('error', (error) => {
        console.error('❌ WebSocket error:', error)
        this.emitEvent('error', error)
      })

      return true

    } catch (error) {
      console.error('💥 WebSocket initialization error:', error)
      return false
    }
  }

  /**
   * Diskonektovanje od servera
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.connected = false
      console.log('🔌 WebSocket manually disconnected')
    }
  }

  /**
   * Slanje custom event-a serveru
   */
  emit(event, data) {
    if (this.socket && this.connected) {
      this.socket.emit(event, data)
    } else {
      console.warn('⚠️ Cannot emit, WebSocket not connected')
    }
  }

  /**
   * Slušač za event-e
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  /**
   * Uklanjanje slušača
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const listeners = this.listeners.get(event)
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  /**
   * Emitovanje event-a lokalno (unutar aplikacije)
   */
  emitEvent(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data))
    }
  }

  /**
   * Priključivanje u sobu za kviz
   */
  joinQuizRoom(quizId) {
    if (this.socket && this.connected) {
      this.socket.emit('join_quiz_room', { quiz_id: quizId })
      console.log(`🎮 Joined quiz room: ${quizId}`)
    }
  }

  /**
   * Napuštanje sobe za kviz
   */
  leaveQuizRoom(quizId) {
    if (this.socket && this.connected) {
      this.socket.emit('leave_quiz_room', { quiz_id: quizId })
      console.log(`🚪 Left quiz room: ${quizId}`)
    }
  }

  /**
   * Slanje notifikacije adminu
   */
  notifyAdmin(message, type = 'info') {
    if (this.socket && this.connected) {
      this.socket.emit('admin_notification', {
        message,
        type,
        timestamp: new Date().toISOString()
      })
    }
  }

  /**
   * Provera da li je konektovan
   */
  isConnected() {
    return this.connected && this.socket?.connected
  }

  /**
   * Dobijanje socket ID-ja
   */
  getSocketId() {
    return this.socket?.id || null
  }
}

// Export kao singleton
const websocketService = new WebSocketService()
export default websocketService