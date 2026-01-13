import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // Vite default port (ili 3000 ako hoćeš)
    host: true, // Da radi na svim network interface-ima
    strictPort: false, // Ne baci error ako je port zauzet
    proxy: {
      '/api': {
        target: 'http://localhost:5000', // Tvoj Flask backend
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,
      },
      '/uploads': {
        target: 'http://localhost:5000', // Za slike
        changeOrigin: true,
        secure: false,
      },
      '/socket.io': {
        target: 'ws://localhost:5000', // WebSocket proxy
        ws: true,
        changeOrigin: true,
      }
    },
    watch: {
      usePolling: true, // Za Docker/WSL
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true, // Za debugging u production
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': '/src', // Za @ imports
    }
  }
})