// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 批3门与闸 C 块 — 私域入口显性化
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI176-B3-GATE-001 §四
//   判据: 未登录点入口 → 明确引导登录（⛔ 空白/报错页）；非 operator → 明确无权限（⛔ 露内容）；
//         operator → 可达且六栏齐；⛔ 隐藏入口≠权限控制；⛔ 私域内容出现在公域
// =============================================================================
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
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

function login() {
  localStorage.setItem('tdca_auth_did', 'TDID-H-0001')
  localStorage.setItem('tdca_auth_token', 'TDCA-CRT-test')
}

function wm(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:demo', data_nature: 'simulated' }
}

/** role：'none' 未登录（502 兜底）；'viewer'；'operator' */
function mockBackend(role: 'none' | 'viewer' | 'operator') {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const u = String(url)
    if (role === 'none') return new Response('{}', { status: 502 })
    if (u.includes('/api/v1/me/dashboard')) {
      return Response.json(wm({ session: { username: 'u1', role, expires_at: '' } }))
    }
    if (u.includes('/api/v1/ops/redlines')) {
      if (role !== 'operator') return new Response('{}', { status: 403 })
      return Response.json(wm({ red_lines: [{ key: 'k1', name: '红线一', index: 'idx' }] }))
    }
    if (u.includes('/api/v1/ops/logs/today')) return Response.json(wm({ filled: true, missing_streak: 0 }))
    return new Response('{}', { status: 502 })
  }))
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  localStorage.clear()
  vi.unstubAllGlobals()
})

describe('批3 C块：导航露出私域入口（我的／运维）', () => {
  it('APP_NAV 含「私域」组：/me 与 /ops 两项', async () => {
    const { APP_NAV } = await import('@/app/app-shell')
    const priv = APP_NAV.find((e) => e.kind === 'group' && e.group === '私域')
    expect(priv).toBeDefined()
    if (priv?.kind === 'group') {
      expect(priv.items.map((i) => i.to)).toEqual(['/me', '/ops'])
    }
    // 评审页仍不入公共导航（运维分区作业页照旧）
    const all = APP_NAV.flatMap((e) => (e.kind === 'link' ? [{ to: e.to }] : e.items))
    expect(all.some((i) => i.to === '/review')).toBe(false)
  })
})

describe('批3 C块：/ops 门三态', () => {
  it('未登录：明确引导登录（去登录链接），⛔ 空白/报错页；不露管理面内容', () => {
    mockBackend('none')
    renderAt('/ops')
    expect(screen.getByTestId('ops-admin-only')).toBeInTheDocument()
    expect(screen.getByTestId('ops-login-link')).toHaveTextContent('去登录')
    expect(screen.queryByTestId('ops-redlines')).not.toBeInTheDocument()
  })

  it('非 operator（viewer）：明确无权限提示，不露内容', async () => {
    mockBackend('viewer')
    login()
    renderAt('/ops')
    await screen.findByTestId('ops-admin-only')
    expect(screen.getByTestId('ops-admin-only')).toHaveTextContent('须管理员身份登录后可见')
    expect(screen.queryByTestId('ops-redlines')).not.toBeInTheDocument()
    expect(screen.queryByTestId('ops-tickets')).not.toBeInTheDocument()
  })

  it('operator：可达，门内入口与红线条齐', async () => {
    mockBackend('operator')
    login()
    renderAt('/ops')
    await screen.findByTestId('ops-redlines')
    expect(await screen.findByText('红线一')).toBeInTheDocument()
    expect(screen.getByTestId('ops-me-entry')).toBeInTheDocument()   // 门内六栏入口
    await screen.findByTestId('ops-logs-entry')                       // 二次拉取（今日日志），需等待
  })
})

describe('批3 C块：门内六栏（/ops/me）建设中标注', () => {
  it('六栏齐＋每栏标「建设中」＋预计批次', () => {
    renderAt('/ops/me')
    for (const key of ['ops-me-site', 'ops-me-service', 'ops-me-governance', 'ops-me-audit', 'ops-me-emergency', 'ops-me-account']) {
      expect(screen.getByTestId(key)).toBeInTheDocument()
      expect(screen.getByTestId(`${key}-building`)).toHaveTextContent('建设中')
    }
    expect(screen.getAllByText(/预计批次：未定（随运维制度件转正排期）/)).toHaveLength(6)
  })
})
