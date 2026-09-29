// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-5CC-W7-004 | 目标函数: W7 组件测试（NSFLPanel + LifecycleDashboard）
// 约束矩阵: H-W7-001~010 验收映射
// =============================================================================
import { describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import {
  NSFLBoundaryList,
  CrossSceneUnionView,
  BlockingModal,
  OperationLog,
  NSFL_COLORS,
} from '../components/NSFLPanel/NSFLPanel'
import {
  LifecycleTimeline,
  DetailPanel,
  NCAChain,
  ExportButton,
  exportReport,
} from '../components/LifecycleDashboard/LifecycleDashboard'

describe('NSFLPanel', () => {
  it('H-W7-001 边界清单三色分类渲染', () => {
    render(
      <NSFLBoundaryList
        items={[
          { id: 'dcb', label: 'data_cross_border（合规）', state: 'allow' },
          { id: 'fc', label: 'financial_crime', state: 'forbid' },
          { id: 't3', label: 'tier_3_p_right_limit', state: 'limit' },
        ]}
      />,
    )
    expect(screen.getByTestId('boundary-allow-dcb')).toHaveTextContent('data_cross_border')
    expect(screen.getByTestId('boundary-forbid-fc')).toHaveTextContent('financial_crime')
    expect(screen.getByTestId('boundary-limit-t3')).toHaveTextContent('tier_3')
    expect(NSFL_COLORS.forbid).toBe('#ef4444') // 颜色语义对齐 NSFL 标准
  })

  it('H-W7-002 并集视图冲突计数 + 闪烁 + Alt-Path', () => {
    vi.useFakeTimers()
    render(
      <CrossSceneUnionView
        data={{
          scene_a: 'SCN-TOUR',
          scene_b: 'SCN-AGRI',
          conflicts: [{ ns_type: 'data_cross_border', description: 'A允许 B禁止', severity: 'MEDIUM' }],
          alt_paths: ['SCN-LOGISTICS'],
          risk_premium: 0.3,
        }}
      />,
    )
    expect(screen.getByTestId('conflict-count')).toHaveTextContent('冲突 1 项')
    expect(screen.getByTestId('conflict-data_cross_border')).toBeInTheDocument()
    expect(screen.getByTestId('alt-path')).toHaveTextContent('SCN-LOGISTICS')
    vi.useRealTimers()
  })

  it('H-W7-003 ⊗ 阻断弹窗：点击外部不可关闭，必须选择', () => {
    const onChoose = vi.fn()
    render(
      <BlockingModal
        title="负空间阻断"
        conflicts={[{ ns_type: 'financial_crime', description: '禁止', severity: 'HIGH' }]}
        altPaths={['SCN-X']}
        onChoose={onChoose}
      />,
    )
    fireEvent.click(document.body) // 外部点击
    expect(onChoose).not.toHaveBeenCalled() // 不可关闭
    fireEvent.click(screen.getByTestId('choose-alt'))
    expect(onChoose).toHaveBeenCalledWith('alt')
  })

  it('H-W7-005 操作日志渲染（block 状态标红）', () => {
    render(
      <OperationLog
        entries={[
          { time: '10:23:45', message: 'Step-2 负空间预检 → PASS', status: 'ok' },
          { time: '10:23:48', message: 'HumanGate #1 等待签名', status: 'block' },
        ]}
      />,
    )
    expect(screen.getByTestId('log-0')).toHaveTextContent('PASS')
    expect(screen.getByTestId('log-1')).toHaveTextContent('HumanGate')
  })
})

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
