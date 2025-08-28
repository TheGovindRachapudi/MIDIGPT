import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  root: './frontend',
  server: {
    port: 3000,
    proxy: {
      '/generate': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/search-songs': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/analyze-track': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/static/generated': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(
      process.env.NODE_ENV === 'production' 
        ? process.env.VITE_API_URL || 'https://your-backend-url.com'
        : 'http://localhost:5000'
    )
  }
})
