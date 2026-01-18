import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Routing
import { BrowserRouter } from 'react-router-dom'

// Date picker
import { LocalizationProvider } from '@mui/x-date-pickers'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'

// React Query (za API caching i state management)
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

// Toast notifications
import { Toaster } from 'react-hot-toast'

//  React Query client sa konfiguracijom
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minuta
      cacheTime: 10 * 60 * 1000, // 10 minuta
      retry: 2, // Pokušaj ponovo 2 puta ako API call fail-uje
      refetchOnWindowFocus: false, // Ne refetch-uj kada se vratiš na tab
      refetchOnReconnect: true, // Refetch kada se konekcija vrati
      refetchOnMount: true, // Refetch kada se komponenta mount-uje
    },
    mutations: {
      retry: 1, // Pokušaj ponovo 1 put za mutacije
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* React Query Provider */}
    <QueryClientProvider client={queryClient}>
      {/* Browser Router za rute */}
      <BrowserRouter>
        {/* Date picker provider */}
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          {/* Globalne toast notifikacije */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
                borderRadius: '8px',
                fontSize: '14px',
                maxWidth: '500px',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#4caf50',
                  secondary: '#fff',
                },
                style: {
                  background: '#2e7d32',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#f44336',
                  secondary: '#fff',
                },
                style: {
                  background: '#d32f2f',
                },
              },
              loading: {
                duration: Infinity, 
                style: {
                  background: '#1976d2',
                },
              },
            }}
          />
          
          {/* Glavna aplikacija */}
          <App />
        </LocalizationProvider>
      </BrowserRouter>
      
      {/* React Query Devtools  */}
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  </React.StrictMode>
)