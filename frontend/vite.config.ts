import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const proxyTarget = process.env.API_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: process.env.HOST || undefined,
    proxy: {
      '/api/v1': proxyTarget,
      '/health': proxyTarget,
      '/audio': proxyTarget,
    },
  },
})
