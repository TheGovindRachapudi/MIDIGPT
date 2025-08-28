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
  }
})
