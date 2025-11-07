// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    hmr: {
      host: '127.0.0.1',
    },
    proxy: {
      '/api': {
        // 👇 AQUI ESTÁ A CORREÇÃO
        // Mude o target de '127.0.0.1' para 'localhost'
        // para que o proxy e o cookie do Flask fiquem no mesmo domínio.
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        rewrite: p => p.replace(/^\/api/, ''),
      },
    },
  },
})