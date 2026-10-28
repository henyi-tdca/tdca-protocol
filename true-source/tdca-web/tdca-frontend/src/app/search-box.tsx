// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 批3 A块 — 页头常驻工具条层搜索入口
// 约束矩阵: L1SI177 SITE-FIND-CODE-001 §二.1（搜索入口落页头工具条层；⛔ 不动导航结构；
//          一行 flex-nowrap，窄屏不霸屏）
// SPDX-License-Identifier: TDCA-Internal
// =============================================================================
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'

/** 页头工具条层搜索框：提交进 /search?q=（本地检索页）；常驻、匿名可用 */
export function SearchBox() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    const v = q.trim()
    navigate(v ? `/search?q=${encodeURIComponent(v)}` : '/search')
  }
  return (
    <form data-testid="header-search" onSubmit={onSubmit} className="flex min-w-0 flex-nowrap items-center gap-1">
      <input
        data-testid="header-search-input"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="全站检索"
        aria-label="全站检索"
        className="h-8 w-28 min-w-0 rounded-lg border border-gray-200 bg-white px-2 text-xs text-gray-800 placeholder:text-gray-400 outline-none focus:border-blue-400 md:w-40"
      />
      <button
        data-testid="header-search-btn"
        type="submit"
        className="h-8 shrink-0 rounded-lg bg-slate-800 px-2.5 text-xs font-medium text-white hover:bg-slate-700"
      >
        搜索
      </button>
    </form>
  )
}
