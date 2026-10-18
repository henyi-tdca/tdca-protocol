// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F2 观测层测试（A-10 接线 + 五面板确权灯 + 拓扑降级）
// 约束矩阵: FRAMEWORK-001 §四 /agents + REV-002 §8B.5 + ID92
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AgentsPage } from '@/pages/AgentsCluster'

// jsdom 无 canvas/布局测量——cytoscape stub（布局计算可跳过，仅验证组件挂载）
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

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-08-12T00:00:00Z', data_nature: 'simulated' }
}

beforeEach(() => {
  localStorage.clear()
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (!String(url).includes('/api/v1/eios/cluster-status')) throw new Error('unexpected url')
    return {
      ok: true,
      status: 200,
      json: async () =>
        envelope({
          cluster: [
            { endpoint: 'eios/trade', capability: '配置权交易', id: 'ID25-01', status: 'READY' },
            { endpoint: 'eios/cognize', capability: '经济认知', id: 'ID25-02', status: 'READY' },
            { endpoint: 'eios/audit', capability: '审计', id: 'ID25-03', status: 'FAIL' },
          ],
          note: 'eios GenieAPI 十端点',
        }),
    } as Response
  }))
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('F2 观测层 /agents', () => {
  it('A-10 集群能力状态渲染（READY/FAIL 标注）', async () => {
    render(<AgentsPage />)
    await waitFor(() => expect(screen.getByTestId('agents-cluster')).toBeInTheDocument())
    expect(screen.getByText('配置权交易')).toBeInTheDocument()
    expect(screen.getAllByText('READY')).toHaveLength(2)
    expect(screen.getByText('FAIL')).toBeInTheDocument()
  })

  it('五大智能体面板 + 确权状态灯（valid/expiring）', async () => {
    render(<AgentsPage />)
    await waitFor(() => expect(screen.getByTestId('agents-panels')).toBeInTheDocument())
    expect(screen.getByText('培训导师')).toBeInTheDocument()
    expect(screen.getByText('效用精灵')).toBeInTheDocument()
    const panels = screen.getByTestId('agents-panels')
    expect(panels.querySelector('[data-panel="Trainer"] [data-attestation]')).toHaveAttribute('data-attestation', 'valid')
    expect(panels.querySelector('[data-panel="Service"] [data-attestation]')).toHaveAttribute('data-attestation', 'expiring')
  })

  it('协作拓扑挂载（TopologyEngine 复用，脱敏数据）', async () => {
    render(<AgentsPage />)
    await waitFor(() => expect(screen.getByTestId('agents-topology')).toBeInTheDocument())
    expect(screen.getByText(/主体哈希化脱敏/)).toBeInTheDocument()
  })

  it('A-10 后端不可用 → fail-closed 提示（ID85）', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => {
      throw new Error('network down')
    }))
    render(<AgentsPage />)
    await waitFor(() => expect(screen.getByTestId('agents-fail-closed')).toBeInTheDocument())
  })
})
