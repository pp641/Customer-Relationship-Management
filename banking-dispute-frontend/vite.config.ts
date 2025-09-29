import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true, // Allow external connections
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => {
          const newPath = path.replace(/^\/api/, '');
          console.log(`Rewriting: ${path} → ${newPath}`);
          return newPath;
        },
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            console.log('❌ Proxy error:', err.message);
            console.log('❌ Target URL:', req.url);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log(`🔄 Proxying: ${req.method} ${req.url} → http://127.0.0.1:8000${req.url.replace('/api', '')}`);
          });
          
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log(`✅ Response: ${proxyRes.statusCode} for ${req.url}`);
          });
        },
      }
    }
  }
})
