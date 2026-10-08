// =============================================================================
// TDCA 制度水印
// FC-ID: KIMI-WEB-DB-TASK-001-M5 + 批1-P1 | 目标函数: 用户控制台 P1 前端测试（me.tsx 扩充面）
// 约束矩阵: 批 1 开工令（人类通道控制台骨架：权属栏 / 判定历史 / AI 意图导航 / 活动产物分页）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { MePage } from '@/pages/me'

function envelope(payload: unknown, nature = 'real') {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-10-09T00:00:00Z', data_nature: nature }
}

const ME_PAYLOAD = {
  session: { username: 'tester', role: 'viewer', expires_at: '2026-10-09T13:30:00+00:00' },
  pending_count: 0,
  my_agents: [],
  my_pending_sign: [],
  my_decided: [],
  my_sandbox: [],
  my_governance: [],
  my_assets: [],
  my_grants: [],
  my_ownership: [
    { record_id: 'OR-SELF-001', work_title: '自研引擎 V1', jurisdiction_branch: 'cn', status: 'registered', nca_ref: 'NCA-OR-001', data_provenance: 'real', created_at: '2026-10-09T00:00:00Z' },
  ],
  my_config_records: [],
  my_points: { balance: 0, data_provenance: 'simulated', note: 't' },
  my_nca: [
    { nca_id: 'NCA-1', action: 'user_register_contract', artifact_path: null, sha256_8: 'aa', ts: '2026-10-09T00:00:00Z' },
  ],
  note: 'test',
}

function mockByUrl(routes: Record<string, unknown>) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    for (const [part, payload] of Object.entries(routes)) {
      if (url.includes(part)) return { ok: true, status: 200, json: async () => envelope(payload) } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
  }))
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('用户控制台 P1（me.tsx 扩充面）', () => {
  it('权属栏渲染本人登记行＋状态标注（后端已本人过滤，前端照单渲染）', async () => {
    mockByUrl({ '/api/v1/me/dashboard': ME_PAYLOAD })
    const { container } = render(<MemoryRouter><MePage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-ownership')).toBeTruthy())
    expect(screen.getByTestId('me-ownership').textContent).toContain('OR-SELF-001')
    expect(screen.getByTestId('me-ownership').textContent).toContain('自研引擎 V1')
    expect(screen.getByTestId('me-ownership').textContent).toContain('🟢 已登记')
    expect(container.querySelector('[data-record="OR-SELF-001"]')).toBeTruthy()
  })

  it('判定历史只列 CLUSTER_ADMIT* 行，其余 action 不进该区', async () => {
    mockByUrl({
      '/api/v1/me/dashboard': {
        ...ME_PAYLOAD,
        my_nca: [
          { nca_id: 'NCA-1', action: 'user_register_contract', artifact_path: null, sha256_8: 'aa', ts: '2026-10-09T00:00:00Z' },
          { nca_id: 'NCA-D1', action: 'CLUSTER_ADMIT_DENY', artifact_path: null, sha256_8: 'bb', ts: '2026-10-09T00:01:00Z' },
          { nca_id: 'NCA-A1', action: 'CLUSTER_ADMIT', artifact_path: null, sha256_8: 'cc', ts: '2026-10-09T00:02:00Z' },
        ],
      },
    })
    render(<MemoryRouter><MePage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-admits')).toBeTruthy())
    const admits = screen.getByTestId('me-admits')
    expect(admits.querySelector('[data-action="CLUSTER_ADMIT_DENY"]')).toBeTruthy()
    expect(admits.querySelector('[data-action="CLUSTER_ADMIT"]')).toBeTruthy()
    expect(admits.textContent).toContain('❌ 未准入')
    expect(admits.textContent).toContain('✅ 准入')
    expect(admits.textContent).not.toContain('user_register_contract')
  })

  it('AI 意图导航：输入 → 命中规则表 → 渲染标题＋直达链接（零模型外呼）', async () => {
    mockByUrl({
      '/api/v1/me/dashboard': ME_PAYLOAD,
      '/api/v1/intent': { matched: true, route: '/toolshelf', title: '工具货架', action: '查询', guide: ['g1', 'g2'], alternatives: [] },
    })
    render(<MemoryRouter><MePage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-assistant')).toBeTruthy())
    fireEvent.change(screen.getByTestId('me-assistant-input'), { target: { value: '我要上架工具' } })
    fireEvent.click(screen.getByTestId('me-assistant-go'))
    await waitFor(() => expect(screen.getByTestId('me-assistant-result')).toBeTruthy())
    expect(screen.getByTestId('me-assistant-result').textContent).toContain('工具货架')
    expect(screen.getByTestId('me-assistant-route').getAttribute('href')).toBe('/toolshelf')
  })

  it('活动产物分页：点「加载更多」追加 /me/nca 明细并显示总数', async () => {
    mockByUrl({
      '/api/v1/me/dashboard': ME_PAYLOAD,
      '/api/v1/me/nca': {
        total: 3,
        items: [
          { nca_id: 'NCA-2', action: 'ownership_register', artifact_path: 'p2', sha256_8: 'dd', ts: '2026-10-09T01:00:00Z' },
          { nca_id: 'NCA-3', action: 'sandbox_apply', artifact_path: 'p3', sha256_8: 'ee', ts: '2026-10-09T02:00:00Z' },
        ],
      },
    })
    render(<MemoryRouter><MePage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-nca')).toBeTruthy())
    expect(screen.getByTestId('me-nca').textContent).not.toContain('NCA-2')
    fireEvent.click(screen.getByTestId('me-nca-more'))
    await waitFor(() => expect(screen.getByTestId('me-nca').textContent).toContain('NCA-2'))
    expect(screen.getByTestId('me-nca').textContent).toContain('NCA-3')
    expect(screen.getByTestId('me-nca').textContent).toContain('共 3 条')
    expect(screen.queryByTestId('me-nca-more')).toBeNull() // 已显齐 → 按钮消失
  })

  it('频道直达条渲染九频道入口', async () => {
    mockByUrl({ '/api/v1/me/dashboard': ME_PAYLOAD })
    const { container } = render(<MemoryRouter><MePage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('me-channels')).toBeTruthy())
    expect(container.querySelectorAll('[data-testid^="me-ch-"]').length).toBe(9)
  })
})
