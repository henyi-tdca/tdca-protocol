// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F5 确权中心测试（总览/meta/dynamic/history + A-11 闭环）
// 约束矩阵: FRAMEWORK-001 §八·B + REV-002 + A-11 契约 + F-4/HUF
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { AttestationOverviewPage, AttestationMetaPage, AttestationDynamicPage, AttestationHistoryPage } from '@/pages/AttestationPage'

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-08-13T00:00:00Z', data_nature: 'simulated' }
}

const QUEUE_PAYLOAD = {
  queue: [
    { request_id: 'DAR-001', agent_id: 'AGENT-007', request_type: 'scene_extension', urgency: 'urgent', reason: 'MRCR 角色扩展' },
    { request_id: 'DAR-002', agent_id: 'AGENT-012', request_type: 'cognition_evolution', urgency: 'normal', reason: 'S 漂移' },
  ],
  total: 2,
  note: '动态确权待审队列',
}

// ATTEST-SCRUB-001 公开视图口径（events：time/event_type/status/summary，⛔ nca_ref/agent 不出）
const HISTORY_PAYLOAD = {
  events: [
    { time: '2026-08-01T00:00:00Z', event_type: '元函数确权', status: 'SIGNED', summary: '已通过' },
    { time: '2026-08-08T00:00:00Z', event_type: '认知演化确权', status: 'REJECTED', summary: '已拒绝（留痕公开）' },
  ],
  total: 2,
  note: '确权历史公开视图（时间／事件类型／公开状态／公开摘要）',
}

function mockApiMulti(pathMap: Record<string, unknown>, failFor?: string) {
  const fn = vi.fn(async (url: string, _init?: RequestInit) => {
    const s = String(url)
    if (failFor && s.includes(failFor)) throw new Error('network down')
    for (const [part, payload] of Object.entries(pathMap)) {
      if (s.includes(part)) {
        return { ok: true, status: 200, json: async () => envelope(payload) } as Response
      }
    }
    throw new Error(`unexpected url ${url}`)
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

const SIX = [
  'objective_function（目标函数）',
  'constraint_matrix（约束矩阵）',
  'prior_distribution（先验分布）',
  'config_boundary（配置权边界）',
  'expected_allocation（预期分配）',
  'audit_trail（审计轨迹）',
]

function checkAllSix() {
  for (const el of SIX) {
    fireEvent.click(screen.getByText(el).previousElementSibling as HTMLElement)
  }
}

beforeEach(() => {
  localStorage.clear()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('F5 确权中心', () => {
  it('总览：待审队列摘要 + 三入口链接（A-11 queue）', async () => {
    mockApiMulti({ '/api/v1/attestation/queue': QUEUE_PAYLOAD })
    render(
      <MemoryRouter initialEntries={['/attestation']}>
        <AttestationOverviewPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('attest-overview')).toBeInTheDocument())
    expect(screen.getByText(/DAR-001/)).toBeInTheDocument()
    expect(screen.getByTestId('link-meta')).toHaveTextContent('元函数初始确权')
    expect(screen.getByTestId('link-dynamic')).toHaveTextContent('1 紧急')
  })

  it('元函数确权：激活系数 + 六要素全勾选 + HUF → POST meta（needHuf）', async () => {
    const fn = mockApiMulti({ '/api/v1/attestation/meta': { status: 'SIGNED', attestation_id: 'META-ATT-ABCD1234', verified: true } })
    render(<AttestationMetaPage />)
    checkAllSix()
    fireEvent.click(screen.getByTestId('meta-huf'))
    expect(screen.getByTestId('huf-modal')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('huf-confirm'))
    await waitFor(() => expect(screen.getByTestId('meta-result')).toHaveTextContent('出盒终裁通过'))
    const [, init] = fn.mock.calls[0]
    const headers = (init as RequestInit).headers as Record<string, string>
    expect(headers.Authorization).toBeDefined()
  })

  it('元函数确权：激活系数 ≤1.2 → REJECTED 展示', async () => {
    mockApiMulti({ '/api/v1/attestation/meta': { status: 'REJECTED', attestation_id: 'META-ATT-X', verified: false } })
    render(<AttestationMetaPage />)
    fireEvent.change(screen.getByTestId('meta-activation'), { target: { value: '1.1' } })
    checkAllSix()
    fireEvent.click(screen.getByTestId('meta-huf'))
    fireEvent.click(screen.getByTestId('huf-confirm'))
    await waitFor(() => expect(screen.getByTestId('meta-result')).toHaveTextContent('拒绝'))
  })

  it('动态确权：紧急度排序 + 四操作 → HUF → POST dynamic 决策更新', async () => {
    const fn = mockApiMulti({
      '/api/v1/attestation/queue': QUEUE_PAYLOAD,
      '/api/v1/attestation/dynamic': { status: 'APPROVED', nca_ref: 'Approval-NCA-ABC' },
    })
    render(<AttestationDynamicPage />)
    await waitFor(() => expect(screen.getByTestId('dynamic-queue')).toBeInTheDocument())
    expect(screen.getByText(/MRCR 角色扩展/)).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('dynamic-queue').querySelector('[data-decision="approve"][data-request-id="DAR-001"]')!)
    expect(screen.getByTestId('huf-modal')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('huf-confirm'))
    await waitFor(() => expect(screen.getByTestId('decision-DAR-001')).toHaveTextContent('APPROVED'))
    const postCall = fn.mock.calls.find((c) => String(c[0]).includes('/api/v1/attestation/dynamic'))
    const headers = (postCall?.[1] as RequestInit | undefined)?.headers as Record<string, string> | undefined
    expect(headers?.Authorization).toBeDefined()
  })

  it('确权历史：NCA 链跨代 + 拒绝事件红色高亮', async () => {
    mockApiMulti({ '/api/v1/attestation/history': HISTORY_PAYLOAD })
    render(<AttestationHistoryPage />)
    await waitFor(() => expect(screen.getByTestId('history-chain')).toBeInTheDocument())
    expect(screen.getByText('元函数确权')).toBeInTheDocument()
    const rejected = screen.getByTestId('history-chain').querySelector('[data-status="REJECTED"]')
    expect(rejected).toHaveClass('bg-red-50')
    expect(rejected).toHaveTextContent('REJECTED')
  })

  it('确权页 fail-closed：后端不可用 → 拒绝渲染', async () => {
    mockApiMulti({ '/api/v1/attestation/queue': QUEUE_PAYLOAD }, '/api/v1/attestation/queue')
    render(
      <MemoryRouter initialEntries={['/attestation']}>
        <AttestationOverviewPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('attest-overview-fail')).toBeInTheDocument())
  })
})
