// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: LABelfIX-001 项二——/ops /studio /governance 三处兜底壳加门
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI223-LABELFIX-001 §二——匿名 ⛔ 兜底壳内容，须登录引导；
//   fail-closed（守卫按 isAuthenticated 判定，未登录/异常一律按匿名挡）；已登录不受影响
// =============================================================================
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router'
import App from '@/App'

// StudioPage 组件链触达 TopologyEngine → cytoscape，jsdom 下桩化（范式同 visual-studio）
vi.mock('cytoscape', () => {
  return { default: vi.fn(() => ({ destroy: vi.fn(), on: vi.fn() })) }
})

function Probe() {
  const loc = useLocation()
  return <div data-testid="loc">{loc.pathname}</div>
}

const ENVELOPE = { data: {}, nca_watermark: 'sha256:test', ts: 't', data_nature: 'simulated' }

describe('LABelfIX-001 项二：三处兜底壳加门', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.unstubAllGlobals()
  })

  it.each(['/ops', '/studio', '/governance'])(
    '匿名直访 %s → 重定向 /auth（登录引导·fail-closed）',
    async (path) => {
      render(
        <MemoryRouter initialEntries={[path]}>
          <App />
          <Probe />
        </MemoryRouter>,
      )
      await waitFor(() => expect(screen.getByTestId('loc').textContent).toBe('/auth'))
    },
  )

  it.each(['/ops', '/studio', '/governance'])(
    '已登录访问 %s → 守卫放行（不拦截）',
    async (path) => {
      localStorage.setItem('tdca_auth_did', 'did:test-ops')
      localStorage.setItem('tdca_auth_token', 'tk-test')
      vi.stubGlobal('fetch', vi.fn(async () => ({
        ok: true, status: 200, json: async () => ENVELOPE,
      })) as unknown as typeof fetch)
      render(
        <MemoryRouter initialEntries={[path]}>
          <App />
          <Probe />
        </MemoryRouter>,
      )
      await waitFor(() => expect(screen.getByTestId('loc').textContent).toBe(path), { timeout: 8000 })
    },
  )
})
