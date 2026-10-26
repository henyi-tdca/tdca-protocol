// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 批3门与闸 B 块 — 机器可读通道七项状态列
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI176-B3-GATE-001 §三（只加一列状态，不改其余文案／版式／区块）
//           判据: 七项各有状态；不存在「声明可用但点不通」之项；docs/{family} 标在线
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import App from '@/App'

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

function mockSiteDocs(payload: unknown) {
  const fn = vi.fn(async (url: string) => {
    if (!String(url).includes('/api/site/docs')) throw new Error(`unexpected url ${url}`)
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

describe('批3 B块：机器可读通道七项状态列', () => {
  it('七项各有状态列：docs 在线（help 族未入站），其余六项在建', () => {
    mockSiteDocs({ items: [] })
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    // 表头新增「状态」列，且仅此一列（端点／说明／状态 三列）
    expect(screen.getByText('状态')).toBeInTheDocument()
    // 在线仅 docs 一项（P-1 实测：七端点仅此项 200）
    expect(screen.getByTestId('home-machine-status--api-site-docs-family')).toHaveTextContent('在线（help 族未入站）')
    // 在建六项
    for (const id of [
      'home-machine-status--api-site-join',
      'home-machine-status--api-site-join-status',
      'home-machine-status--api-site-agent-card-handshake',
      'home-machine-status--api-site-agent-card-id',
      'home-machine-status--api-site-directory',
      'home-machine-status--api-site-meter',
    ]) {
      expect(screen.getByTestId(id)).toHaveTextContent('在建')
    }
    // 不得有「声明可用但点不通」之项：除 docs 外不允许出现「在线」
    const cells = screen.getAllByText(/在线|在建/)
    expect(cells.filter((c) => c.textContent === '在线')).toHaveLength(0)
  })

  it('原有端点与说明文案一字未改', () => {
    mockSiteDocs({ items: [] })
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    for (const [ep, desc] of [
      ['POST /api/site/join', '缔约申请（双通道）'],
      ['GET /api/site/join/status', '缔约进度查询'],
      ['POST /api/site/agent-card/handshake', '智能体首呼握手'],
      ['GET /api/site/agent-card/{id}', '对接卡公开查询'],
      ['GET /api/site/directory', '名册摘要（脱敏）'],
      ['GET /api/site/docs/{family}', '文档目录'],
      ['POST /api/site/meter', '调用计量（仅智能体通道）'],
    ]) {
      expect(screen.getByText(ep)).toBeInTheDocument()
      expect(screen.getByText(desc)).toBeInTheDocument()
    }
  })
})
