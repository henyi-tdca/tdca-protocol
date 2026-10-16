// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-A2 路由骨架测试（15 路由可达 + 404 兜底）
// 约束矩阵: FRAMEWORK-001 §四 + REV-002（15 路由）
// =============================================================================
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '@/App'
import { PAGE_META } from '@/pages/pages'

// /agents 渲染 TopologyEngine（Cytoscape）——jsdom 无布局环境，stub 布局计算
vi.mock('cytoscape', () => {
  const fakeNode = () => ({ position: () => ({ x: 10, y: 10 }), id: () => 'n' })
  const fakeCore = {
    nodes: () => [fakeNode()],
    elements: () => ({
      boundingBox: () => ({ x1: 0, y1: 0, x2: 100, y2: 100 }),
      nodes: () => [fakeNode()],
    }),
    ready: (cb: () => void) => cb(),
    destroy: () => {},
  }
  return { default: () => fakeCore }
})

beforeEach(() => {
  localStorage.clear()
  // F-2 守卫预置登录态（受保护路由 /agents /studio /attestation* /governance 渲染需登录）
  localStorage.setItem('tdca_auth_did', 'TDID-H-0001')
  localStorage.setItem('tdca_auth_token', 'TDCA-CRT-test')
})

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('F0-A2 路由骨架（15 路由 + 404）', () => {
  it('36 路由全部可达且渲染对应页面标题（33 基线 + 批2块二 /docs + 批2块三 /process 与 /me/appeal；15 + F-2 /auth + M4 /register + M5 双后台 + ABT-1 /about + P1 /workbuddy + P2 /cluster + P3 /formal + P4 /toolshelf + P6 /anchors + P7 /ops + P8a /ownership-registry + P8b /authorization-registry + P9 /market-sim + 智能体区 /agent-shelf + 公告栏 /announcements + 文档库 /docs + 流程总览 /process + 申诉 /me/appeal）', () => {
    expect(PAGE_META).toHaveLength(36)
    for (const meta of PAGE_META) {
      const { unmount } = renderAt(meta.path)
      expect(screen.getByRole('heading', { name: meta.title })).toBeInTheDocument()
      unmount()
    }
  })

  it('未知路由 404 兜底', () => {
    renderAt('/no-such-page-xyz')
    expect(screen.getByRole('heading', { name: /404 · 路由未找到/ })).toBeInTheDocument()
  })

  it('确权子路由（/attestation/meta /dynamic /history）可达', () => {
    for (const p of ['/attestation/meta', '/attestation/dynamic', '/attestation/history']) {
      const { unmount } = renderAt(p)
      expect(screen.getByTestId('page-shell')).toBeInTheDocument()
      unmount()
    }
  })

  it('应用壳常驻：导航 / HUF Banner / 层级指示器在每个路由渲染', () => {
    const { unmount } = renderAt('/tax')
    expect(screen.getByTestId('app-nav')).toBeInTheDocument()
    expect(screen.getByTestId('huf-banner')).toBeInTheDocument()
    expect(screen.getByTestId('layer-indicator')).toBeInTheDocument()
    unmount()
  })

  it('路由层级映射：/tax → L3 高亮', () => {
    renderAt('/tax')
    expect(screen.getByTestId('layer-indicator')).toHaveAttribute('data-current', 'L3')
  })

  it('路由层级映射：/ownership → L1；/studio → STUDIO', () => {
    const r1 = renderAt('/ownership')
    expect(screen.getByTestId('layer-indicator')).toHaveAttribute('data-current', 'L1')
    r1.unmount()
    const r2 = renderAt('/studio')
    expect(screen.getByTestId('layer-indicator')).toHaveAttribute('data-current', 'STUDIO')
    r2.unmount()
  })
})
