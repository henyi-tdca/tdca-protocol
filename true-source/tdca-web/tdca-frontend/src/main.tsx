// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0 入口（HashRouter + 应用壳）
// 约束矩阵: FRAMEWORK-001 §二（React Router v7 hash）+ 既有资产继承
// 预期分配: main.tsx（StrictMode + HashRouter + App）
// =============================================================================
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter } from 'react-router'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </StrictMode>,
)
