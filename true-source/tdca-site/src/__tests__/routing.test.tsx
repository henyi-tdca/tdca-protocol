// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-A2 路由骨架测试（15 路由可达 + 404 兜底）
// 约束矩阵: FRAMEWORK-001 §四 + REV-002（15 路由）
// =============================================================================
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import App from '@/App'
import { PAGE_META } from '@/pages/PagesIndex'

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
  it('在册 9 面全部可达且各面渲染标题（册题权威在站点地图逐字呈现）', () => {
    // 对齐令 SITE-TESTFIX-001（甲组）：缩面为有意——PagesIndex 并轨注记自陈「本批四面＋新版既有四面」；
    // 缔约申请页已撤（ACCESS-FIX-001-AMEND-1 交付二：注册已含缔约同意）。旧期望 32 系滞后。
    // MIGRATE 批1（L1SI206）追加 /search 检索面：8→9。
    expect(PAGE_META).toHaveLength(9)
    for (const meta of PAGE_META) {
      const { unmount } = renderAt(meta.path)
      // 逐面可达且渲染至少一枚标题（壳题以页面实读为准：册题与壳题注记差异存在——
      // 如 册题「审查」对页题「缔约审核」、册题「注册（缔约）」对页题「注册（人类账号）」，不判错）
      expect(screen.getAllByRole('heading').length).toBeGreaterThan(0)
      unmount()
    }
    // 册题权威：站点地图逐字呈现 8 条登记标题
    renderAt('/pages')
    for (const meta of PAGE_META) {
      expect(screen.getAllByText((_, el) => el?.textContent === meta.title).length).toBeGreaterThan(0)
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

  it('应用壳常驻：导航在每个路由渲染（HUF Banner 与层级指示器已随 FRONTEND-MERGE 壳改撤出，见 PagesIndex 并轨注记「层级指示器未随迁」）', () => {
    for (const p of ['/tax', '/studio', '/overview']) {
      const { unmount } = renderAt(p)
      expect(screen.getByTestId('app-nav')).toBeInTheDocument()
      unmount()
    }
  })

  it('路由层级数据契约：PAGE_META 逐条带非空 layer 字段（层级指示器已撤，layer 降为纯数据字段）', () => {
    for (const meta of PAGE_META) {
      expect(meta.layer).toMatch(/^\S+$/)
    }
    // 现册 8 面均为 L0（制度橱窗层）；层级映射随未来批次扩面时再按在册值断言
    expect(PAGE_META.every((m) => m.layer === 'L0')).toBe(true)
  })

  it('/ownership 与 /studio 可达且渲染对应面（壳直挂，不设登录门槛——照 FRONTEND-MERGE 批3 核可口径）', () => {
    const r1 = renderAt('/ownership')
    expect(screen.getByTestId('page-shell')).toBeInTheDocument()
    r1.unmount()
    const r2 = renderAt('/studio')
    expect(screen.getByTestId('studio-lifecycle')).toBeInTheDocument()
    r2.unmount()
  })
})
