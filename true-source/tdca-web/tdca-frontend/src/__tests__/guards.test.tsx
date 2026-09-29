// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-A4 六约束模块测试（BV-3/F-4/MOU/HUF/ID93/G-1）
// 约束矩阵: FRAMEWORK-001 §六
// =============================================================================
import { describe, expect, it, vi } from 'vitest'
import { useState } from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import {
  ReadOnlyStream,
  FuseIndicator,
  MouReadout,
  HufModal,
  NotifierRoles,
  TermGuard,
  CompoundCheck,
} from '@/shared/guards'

describe('F0-A4 六约束模块', () => {
  it('ReadOnlyStream（BV-3）：只读渲染且无编辑路径（无按钮/无输入）', () => {
    render(<ReadOnlyStream title="MOU 流" data={{ tax: 1 }} />)
    expect(screen.getByTestId('readonly-stream')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('FuseIndicator（F-4）：BLOCKED 红色灯 / CLOSED 绿色灯', () => {
    const r1 = render(<FuseIndicator state="BLOCKED" />)
    expect(screen.getByTestId('fuse-indicator')).toHaveAttribute('data-state', 'BLOCKED')
    expect(screen.getByTestId('fuse-dot')).toHaveClass('bg-red-600')
    r1.unmount()
    render(<FuseIndicator state="CLOSED" />)
    expect(screen.getByTestId('fuse-dot')).toHaveClass('bg-emerald-500')
  })

  it('MouReadout（ID79）：金额低于硬下限 → 违反告警；达标 → 金色高亮', () => {
    const r1 = render(<MouReadout label="调度税" amount={0} minThreshold={0.01} />)
    expect(screen.getByTestId('mou-readout')).toHaveAttribute('data-violated', 'true')
    expect(screen.getByTestId('mou-violation')).toBeInTheDocument()
    r1.unmount()
    render(<MouReadout label="调度税" amount={200} minThreshold={0} />)
    expect(screen.getByTestId('mou-readout')).toHaveAttribute('data-violated', 'false')
  })

  it('HufModal：取消即中止（onConfirm 不触发）+ 确认触发签批', () => {
    const onConfirm = vi.fn()
    function Harness() {
      const [open, setOpen] = useState(true)
      return <HufModal open={open} onOpenChange={setOpen} onConfirm={onConfirm} />
    }
    const r = render(<Harness />)
    expect(screen.getByTestId('huf-modal')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('huf-cancel'))
    expect(onConfirm).not.toHaveBeenCalled()
    expect(r.container.querySelector('[data-testid="huf-modal"]')).not.toBeInTheDocument()
    // 重新打开 → 确认
    const { rerender } = render(<Harness key="reopen" />)
    void rerender
    fireEvent.click(screen.getByTestId('huf-confirm'))
    expect(onConfirm).toHaveBeenCalledTimes(1)
    expect(r.container.querySelector('[data-testid="huf-modal"]')).not.toBeInTheDocument()
  })

  it('NotifierRoles（ID93）：四角色灯激活状态正确', () => {
    render(<NotifierRoles roles={{ operator: true, gov: false, fin: true, med: false }} sceneCount={3} />)
    expect(screen.getByTestId('notifier-roles')).toBeInTheDocument()
    expect(screen.getByTestId('notifier-roles').querySelector('[data-role="operator"]')).toHaveAttribute('data-active', 'true')
    expect(screen.getByTestId('notifier-roles').querySelector('[data-role="gov"]')).toHaveAttribute('data-active', 'false')
  })

  it('TermGuard（G-1）：文本含无据声称 → 漂移警告', () => {
    render(<TermGuard text="术语防火墙 V2.1（FROZEN-20260808）" />)
    expect(screen.getByTestId('term-guard')).toHaveTextContent('V2.1')
  })

  it('TermGuard（G-1）：干净文本 → 不渲染', () => {
    render(<TermGuard text="配置权市场（TERMS-001 V1.1）" />)
    expect(screen.queryByTestId('term-guard')).not.toBeInTheDocument()
  })

  it('CompoundCheck（ID90）：条件未全满足 → 阻断；全满足 → 通过', () => {
    const conds = [
      { id: 'reuse', label: '复用必要性（ID90）', met: true },
      { id: 'sandbox', label: '沙盒验证完成', met: false },
      { id: 'mou', label: 'MOU 硬数据支撑', met: true },
    ]
    render(<CompoundCheck conditions={conds} />)
    expect(screen.getByTestId('compound-check')).toHaveAttribute('data-blocked', 'true')
    expect(screen.getByTestId('compound-blocked')).toBeInTheDocument()
  })
})
