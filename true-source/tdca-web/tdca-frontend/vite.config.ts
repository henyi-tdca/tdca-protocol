import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// TDCA 前端主应用（F0 框架壳）
// 后端对接: gateway:8100（统一 API 网关，仅消费）
// proxy: /api → 127.0.0.1:8100（B/A 类接口面）
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8100',
      '/ws': { target: 'http://127.0.0.1:8100', ws: true },
      '/health': 'http://127.0.0.1:8100',
      '/handshake': 'http://127.0.0.1:8100',
      '/nca': 'http://127.0.0.1:8100',
      '/nsfl': 'http://127.0.0.1:8100',
      '/cross-scene': 'http://127.0.0.1:8100',
      '/workflow': 'http://127.0.0.1:8100',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    css: false,
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
