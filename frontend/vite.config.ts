import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Use relative base path for GitHub Pages compatibility
  // This works for both root and subdirectory deployments
  base: process.env.NODE_ENV === 'production' 
    ? (process.env.VITE_BASE_PATH || './')
    : '/',
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  server: {
    port: 8000,
  },
})


