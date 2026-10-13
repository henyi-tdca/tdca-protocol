import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
import { inspectAttr } from 'kimi-plugin-inspect-react'

// https://vite.dev/config/
export default defineConfig({
  // FRONTEND-MERGE 批3：BrowserRouter 深链直开须绝对基路径（原 './' 致 /agents/:id 两级深链取不到产物白屏；
  // 站点挂域名根，绝对根基安全；旧版为 hash 路由故从未触发）
  base: '/',
  plugins: [inspectAttr(), react()],
  server: {
    port: 3000,
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
