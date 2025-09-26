import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  preview: {
    host: '0.0.0.0',
    port: 4173,
    allowedHosts: ["*","frontend","localhost", "127.0.0.1"]
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ["*","frontend","localhost", "127.0.0.1"]
  }
})
