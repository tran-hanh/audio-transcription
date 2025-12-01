import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // For GitHub Pages: use repository name as base path
  // For local dev: use root path
  base: process.env.NODE_ENV === 'production' 
    ? (process.env.VITE_BASE_PATH || '/audio-transcription/')
    : '/',
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  server: {
    port: 8000,
  },
})


