// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-5CC-W7-004 | 目标函数: W7 组件测试（LifecycleDashboard 半件）
// 约束矩阵: H-W7-006~010 验收映射
// 拆搬说明：旧 w7.test.tsx 含 NSFLPanel / LifecycleDashboard 两个 describe。
//   本件仅搬 LifecycleDashboard 块（同字照搬，未删用例）；NSFLPanel 块按
//   单B裁定③另案挂账，不删用例凑绿，用例留旧树待挂账案解。
// =============================================================================
import { describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import {
  LifecycleTimeline,
  DetailPanel,
  NCAChain,
  ExportButton,
  exportReport,
} from '@/components/LifecycleDashboard/LifecycleDashboard'

describe('LifecycleDashboard', () => {
  const nodes = [
    { step: 'INIT', label: 'INIT', status: 'ok' as const },
    { step: 'S3', label: 'S3 匹配', status: 'block' as const, detail: { reason: 'INSUFFICIENT_BUDGET' } },
    { step: 'S5', label: 'S5 调度', status: 'pending' as const },
  ]

  it('H-W7-006 时间轴节点点击展开详情', () => {
    const onSelect = vi.fn()
    render(<LifecycleTimeline nodes={nodes} onSelect={onSelect} />)
    fireEvent.click(screen.getByTestId('node-S3'))
    expect(onSelect).toHaveBeenCalledWith(nodes[1])
  })

  it('H-W7-007 异常节点高亮（block 样式）', () => {
    render(<LifecycleTimeline nodes={nodes} onSelect={() => {}} />)
    expect(screen.getByTestId('node-S3')).toHaveStyle({ borderColor: '#ef4444' })
  })

  it('详情面板 + NCA 链接可点击（CP-4/CP-5）', () => {
    render(<DetailPanel node={{ step: 'S3', label: 'S3 匹配', status: 'block', detail: { reason: 'X' }, nca_ref: 'NCA-001' }} />)
    const link = screen.getByTestId('nca-link-NCA-001')
    expect(link).toHaveAttribute('href', 'nca://NCA-001')
  })

  it('NCA 链无断裂', () => {
    render(<NCAChain chain={['NCA-1', 'NCA-2', 'NCA-3']} />)
    expect(screen.getAllByTestId(/^chain-link-/)).toHaveLength(3)
  })

  it('H-W7-010 导出报告 JSON 完整（含 NCA/签名/延迟）', () => {
    const json = exportReport({ request_id: 'HS-001', nodes, nca_chain: ['NCA-1'] })
    const parsed = JSON.parse(json)
    expect(parsed.request_id).toBe('HS-001')
    expect(parsed.nodes.length).toBe(3)
    expect(parsed.nca_chain).toEqual(['NCA-1'])
    render(<ExportButton data={{ request_id: 'HS-001', nodes, nca_chain: ['NCA-1'] }} />)
    expect(screen.getByTestId('export-button')).toBeInTheDocument()
  })
})
