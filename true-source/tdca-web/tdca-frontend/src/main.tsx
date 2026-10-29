// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0 入口（BrowserRouter 历史模式 + 应用壳）
// 约束矩阵: SITE-SEO-A-001 乙-1——/about 式干净地址（⛔ #）；旧 #/xxx 深链接自动跳新址
//   （保留至少一个版本周期）；服务器回退 try_files 属部署面配套（本令 ⛔ 不部署，回报记前置条件）
// =============================================================================
// 旧地址兼容（先于路由初始化执行）：命中老 #/xxx 深链接 → 自动跳到对应新历史地址
;(function () {
  const h = window.location.hash
  if (h.indexOf('#/') === 0) {
    const target = h.slice(1) // '#/about?x=1' → '/about?x=1'
    window.location.replace(target.indexOf('?') === -1 ? target + window.location.search : target)
  }
})()

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
