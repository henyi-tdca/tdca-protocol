// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 乙案 P2 运维日志前端测试（表单六组＋红点）
// 约束矩阵: TDCA-HANDOFF-OPS-STORAGE-P2-001 §四；键名与机读版模板同源
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { OpsLogsPage } from '@/pages/ops-logs'
import { OpsPage } from '@/pages/ops'

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-10-17T00:00:00Z', data_nature: 'real' }
}

const GROUP_HEADS = ['A 基本信息', 'B 技术运维', 'C 内容运维', 'D 运营运维', 'E 安全合规', 'F 异常与收尾']

function mockAll(today: { filled: boolean; missing_streak: number }) {
  vi.stubGlobal('fetch', vi.fn(async (url: string, opts?: RequestInit) => {
    const u = String(url)
    if (u.includes('/api/v1/me/dashboard')) {
      return { ok: true, status: 200, json: async () => envelope({ session: { role: 'operator' } }) } as Response
    }
    if (u.includes('/api/v1/ops/logs/today')) {
      return { ok: true, status: 200, json: async () => envelope({ date: '2026-10-17', ...today }) } as Response
    }
    if (u.includes('/api/v1/ops/logs') && opts?.method === 'POST') {
      return { ok: true, status: 201, json: async () => envelope({ log_date: '2026-10-17', duty_no: 'OP-001', exceptions_count: 0, unclosed_count: 0 }) } as Response
    }
    if (u.includes('/api/v1/ops/logs') && !u.includes('/today')) {
      return { ok: true, status: 200, json: async () => envelope({ total: 0, logs: [] }) } as Response
    }
    if (u.includes('/api/v1/ops/redlines')) {
      return { ok: true, status: 200, json: async () => envelope({ count: 8, red_lines: [] }) } as Response
    }
    if (u.includes('/api/v1/ops/tickets')) {
      return { ok: true, status: 200, json: async () => envelope({ count: 0, tickets: [] }) } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
  }))
}

const fetchMock = () => vi.mocked(fetch)

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('乙案 P2 · 运维日志表单（/ops/logs）', () => {
  it('六组齐、键名同源；提交体含 A~F 六组与值班信息', async () => {
    mockAll({ filled: false, missing_streak: 1 })
    render(<MemoryRouter><OpsLogsPage /></MemoryRouter>)
    for (const g of GROUP_HEADS) expect(screen.getByText(g)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByTestId('ops-logs-unfilled')).toBeInTheDocument())

    fireEvent.change(screen.getByTestId('f-duty_role').querySelector('input')!, { target: { value: '值班运维' } })
    fireEvent.change(screen.getByTestId('f-duty_no').querySelector('input')!, { target: { value: 'OP-001' } })
    fireEvent.change(screen.getByTestId('f-handover').querySelector('input')!, { target: { value: '备份运维+OP-002' } })
    fireEvent.change(screen.getByTestId('f-cert_not_after').querySelector('input')!, { target: { value: '2027-01-15' } })
    fireEvent.change(screen.getByTestId('f-cert_days_left').querySelector('input')!, { target: { value: '90' } })
    fireEvent.change(screen.getByTestId('f-backup_name').querySelector('input')!, { target: { value: 'dist-bak' } })
    fireEvent.change(screen.getByTestId('f-backup_sha').querySelector('input')!, { target: { value: '0'.repeat(16) } })

    fireEvent.click(screen.getByTestId('ops-logs-submit'))
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('已入库'))
    const post = fetchMock().mock.calls.find(([, o]) => (o as RequestInit)?.method === 'POST')
    const body = JSON.parse(String((post![1] as RequestInit).body))
    for (const g of ['A_基本信息', 'B_技术运维', 'C_内容运维', 'D_运营运维', 'E_安全合规', 'F_异常与收尾']) {
      expect(body.sections[g]).toBeDefined()
    }
    expect(body.duty_role).toBe('值班运维')
    expect(body.sections.A_基本信息.duty_role).toBe('值班运维+OP-001')
  })

  it('异常项三段三格；未闭合展开下一步+时限', async () => {
    mockAll({ filled: true, missing_streak: 0 })
    render(<MemoryRouter><OpsLogsPage /></MemoryRouter>)
    fireEvent.click(screen.getByText('＋ 添加异常项（三段：发现→处置→闭合）'))
    expect(screen.getByTestId('ex-0')).toBeInTheDocument()
    expect(screen.getByTestId('f-ex0_next')).toBeInTheDocument()   // 默认未闭合 ⟹ 必填项展开
    expect(screen.getByTestId('f-ex0_deadline')).toBeInTheDocument()
  })
})

describe('乙案 P2 · 运维端红点（/ops 首页）', () => {
  it('今日未填 → 🔴；连续≥2 日 → 升级横幅', async () => {
    mockAll({ filled: false, missing_streak: 3 })
    render(<MemoryRouter><OpsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ops-logs-red-dot')).toBeInTheDocument())
    expect(screen.getByTestId('ops-logs-escalation')).toHaveTextContent('连续 3 日未填')
    expect(screen.getByText('运维日志（每日填写）')).toBeInTheDocument()
  })

  it('今日已填 → 无红点', async () => {
    mockAll({ filled: true, missing_streak: 0 })
    render(<MemoryRouter><OpsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ops-logs-entry')).toBeInTheDocument())
    expect(screen.queryByTestId('ops-logs-red-dot')).not.toBeInTheDocument()
  })
})
