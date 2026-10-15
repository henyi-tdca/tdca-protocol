// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F3 Agent Studio 通道六步实况接真（批 4 块一）
// 约束矩阵: 批 4 令 17/18（未达不虚报·模拟水印保留·对外词面零内部编号）
// 拆搬说明：本件只测新增「通道六步实况」区块；既有 studio-f3 六用例一字未动。
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { StudioPage } from '@/pages/StudioPage'

vi.mock('cytoscape', () => {
  const fakeNode = () => ({ position: () => ({ x: 10, y: 10 }), id: () => 'n' })
  const fakeCore = {
    nodes: () => [fakeNode()],
    elements: () => ({ boundingBox: () => ({ x1: 0, y1: 0, x2: 100, y2: 100 }), nodes: () => [fakeNode()] }),
    ready: (cb: () => void) => cb(),
    destroy: () => {},
  }
  return { default: () => fakeCore }
})

function envelope(payload: unknown, nature = 'mixed') {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-10-16T00:00:00Z', data_nature: nature }
}

function mockGate(payload: unknown, fail = false) {
  const fn = vi.fn(async (url: string, _init?: RequestInit) => {
    if (fail) throw new Error('network down')
    if (!url.includes('/api/v1/agent-channel/gate/')) throw new Error(`unexpected url ${url}`)
    return { ok: true, status: 200, json: async () => envelope(payload) } as Response
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

function renderStudio() {
  return render(
    <MemoryRouter>
      <StudioPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('批 4 块一 · 通道六步实况接真（/studio）', () => {
  it('实况呈现：已达/未达如实标注（未达步 ⛔ 不显示为已达）', async () => {
    mockGate({
      reg_no: 'TEST-REG-1',
      grants_active: 1,
      metering: { units_total: 5, data_nature: 'simulated' },
      gate: {
        admitted: false,
        steps: {
          'protocol-load': { step: '①', label: '加载协议', state: 'satisfied' },
          token: { step: '②', label: '持根节点执行令牌', state: 'satisfied' },
          'ns-review': { step: '③', label: '负空间审查', state: 'satisfied' },
          sandbox: { step: '④', label: '沙盒验证', state: 'satisfied' },
          execute: { step: '⑤', label: '正空间执行', state: 'pending' },
          'nca-evidence': { step: '⑥', label: 'NCA 存证', state: 'satisfied' },
        },
      },
    })
    renderStudio()
    fireEvent.change(screen.getByTestId('channel-gate-input'), { target: { value: 'TEST-REG-1' } })
    fireEvent.click(screen.getByTestId('channel-gate-query'))
    await waitFor(() => expect(screen.getByTestId('channel-gate-steps')).toBeInTheDocument())
    // 已达步如实
    expect(screen.getByTestId('channel-gate-step-protocol-load')).toHaveTextContent('已达')
    // 未达步如实显示「未达」，⛔ 不得显示为已达
    expect(screen.getByTestId('channel-gate-step-execute')).toHaveTextContent('未达')
    expect(screen.getByTestId('channel-gate-step-execute')).not.toHaveTextContent('已达')
    // 授权件与计量（模拟）如实呈现；总闸未全达如实
    expect(screen.getByTestId('channel-gate-grants')).toHaveTextContent('1 件')
    expect(screen.getByTestId('channel-gate-units')).toHaveTextContent('5')
    expect(screen.getByTestId('channel-gate-admitted')).toHaveTextContent('未全达')
  })

  it('后端不可用 → fail-closed 提示（不猜测数据）', async () => {
    mockGate({}, true)
    renderStudio()
    fireEvent.change(screen.getByTestId('channel-gate-input'), { target: { value: 'TEST-REG-2' } })
    fireEvent.click(screen.getByTestId('channel-gate-query'))
    await waitFor(() => expect(screen.getByTestId('channel-gate-error')).toBeInTheDocument())
    expect(screen.getByTestId('channel-gate-error')).toHaveTextContent('fail-closed')
    expect(screen.queryByTestId('channel-gate-steps')).not.toBeInTheDocument()
  })

  it('页面词面不含通道内部编号体例样例（对外词面零内部编号）', () => {
    mockGate({})
    renderStudio()
    const section = screen.getByTestId('channel-gate-section')
    expect(section.textContent).not.toMatch(/SAR-|SCD-|SGR-|TDID-/)
  })
})
