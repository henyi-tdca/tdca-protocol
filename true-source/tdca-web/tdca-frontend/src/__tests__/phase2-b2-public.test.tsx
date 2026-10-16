// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批2块二 — 公域页面移植验收测试
// 约束矩阵: TDCA-FINAL-SITE-PHASE2-REVAMP-001-B2 §二块二 + §一裁点2（文档库与文库并存）
// =============================================================================
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import App from '@/App'

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

function mockSiteDocs(payload: unknown, fail = false) {
  const fn = vi.fn(async (url: string) => {
    if (!String(url).includes('/api/site/docs')) throw new Error(`unexpected url ${url}`)
    if (fail) throw new Error('network down')
    return { ok: true, status: 200, json: async () => payload } as Response
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

beforeEach(() => {
  localStorage.clear()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('二期改版批2块二：首页正版门户内容', () => {
  it('首屏＋三体＋合规三阶＋双通道＋机器可读＋总览区全段在位', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: 'TDCA 三体可视化中心' })).toBeInTheDocument()
    expect(screen.getByText('三个面，一个中心')).toBeInTheDocument()
    expect(screen.getByText('合规前置：缔约三阶')).toBeInTheDocument()
    expect(screen.getByText('双通道缔约')).toBeInTheDocument()
    expect(screen.getByText('机器可读通道')).toBeInTheDocument()
    expect(screen.getByText('制度总览 · 四层架构（L0 法律底层 → L1 所有权 → L2 配置权 → L3 效用计量）')).toBeInTheDocument()
  })

  it('栏目中文口径：workbuddy 面已改人机协作面', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByText('人机协作面')).toBeInTheDocument()
  })
})

describe('二期改版批2块二：文档库（与文库并存）', () => {
  it('/docs 首页两族在位（制度／帮助）', () => {
    render(
      <MemoryRouter initialEntries={['/docs']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: '文档库' })).toBeInTheDocument()
    expect(screen.getByText('制度／条例／规则／办法／章程／指引')).toBeInTheDocument()
    expect(screen.getByText('说明／示例／帮助')).toBeInTheDocument()
  })

  it('/docs/:family 列表渲染（mock 只读面）', async () => {
    mockSiteDocs({ items: [{ slug: 'a', title: '示例件 A', synced_at: '2026-10-16' }] })
    render(
      <MemoryRouter initialEntries={['/docs/help']}>
        <App />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('docs-index')).toBeInTheDocument())
    expect(screen.getByText('示例件 A')).toBeInTheDocument()
  })

  it('/docs/:family/:slug 详情渲染正文（纯文本呈现）', async () => {
    mockSiteDocs({ title: '帮助件', body_md: '# 标题\n正文两行', source_path: 'docs/help/x.md', synced_at: '2026-10-16' })
    render(
      <MemoryRouter initialEntries={['/docs/help/x']}>
        <App />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('doc-body')).toBeInTheDocument())
    expect(screen.getByTestId('doc-body').textContent).toContain('正文两行')
  })

  it('文档库 fail-closed：只读面不可用即明示', async () => {
    mockSiteDocs({}, true)
    render(
      <MemoryRouter initialEntries={['/docs/help']}>
        <App />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('docs-fail-closed')).toBeInTheDocument())
  })
})

describe('二期改版批2块二：帮助与联系（复用帮助族）', () => {
  it('帮助条目动态列出，联系块不预置（如实空栏）', async () => {
    mockSiteDocs({
      items: [
        { slug: 'howto', title: '如何注册', synced_at: '2026-10-16' },
        { slug: 'contact', title: '联系我们', synced_at: '2026-10-16' },
      ],
    })
    render(
      <MemoryRouter initialEntries={['/help']}>
        <App />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('help-list')).toBeInTheDocument())
    expect(screen.getByText('如何注册')).toBeInTheDocument()
    // 含「联系」条目 ⟹ 联系块列出该条目
    expect(screen.getByTestId('help-contact').textContent).toContain('联系我们')
  })

  it('帮助族为空时联系块如实空栏（⛔ 不预置渠道）', async () => {
    mockSiteDocs({ items: [] })
    render(
      <MemoryRouter initialEntries={['/help']}>
        <App />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('help-contact')).toBeInTheDocument())
    expect(screen.getByTestId('help-contact').textContent).toContain('未入站')
  })
})

describe('二期改版批2块二：模拟锚入公域（裁定落地件）', () => {
  it('资源组含模拟锚；anchors 页公域可达', () => {
    render(
      <MemoryRouter initialEntries={['/anchors']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: '模拟外部锚与版权事件（P6）' })).toBeInTheDocument()
    expect(screen.getByTestId('app-nav').textContent).toContain('模拟锚')
  })
})
