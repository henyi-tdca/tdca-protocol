// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-CHANNEL-MY-001 | 目标函数: L1SI167-CHANNEL-UI-001 判成自测
// 约束矩阵: 判成五条（四步走完每步可见／置灰+人话／令牌只显一次／零内部编号）
// 说明: mock 掉 api 客户端（不走真网络）；演示档与真跑档前置灯两路各验
// =============================================================================
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

// —— 后端实况剧本（真跑档用） ——
const GATE_FRESH = {
  reg_no: 'SAR-TEST000001',
  channel_type: 'ANCHOR',
  promoted: false,
  promoted_at: null,
  gate: {
    admitted: false,
    steps: {
      'protocol-load': { step: 1, label: '协议加载', state: 'satisfied' },
      token: { step: 2, label: '令牌', state: 'satisfied' },
      'ns-review': { step: 3, label: '负空间审查', state: 'pending' },
      sandbox: { step: 4, label: '沙盒', state: 'pending' },
      execute: { step: 5, label: '执行', state: 'pending' },
      'nca-evidence': { step: 6, label: '存证', state: 'satisfied' },
    },
  },
}
const GATE_READY = {
  ...GATE_FRESH,
  gate: {
    ...GATE_FRESH.gate,
    steps: {
      ...GATE_FRESH.gate.steps,
      'ns-review': { step: 3, label: '负空间审查', state: 'satisfied' },
      sandbox: { step: 4, label: '沙盒', state: 'satisfied' },
    },
  },
}
const DEP_ZERO = { reg_no: 'SAR-TEST000001', effective_mou: 0, frozen_mou: 0, events: [], required_min_mou: 1 }

let gateScript: unknown = GATE_FRESH
let depScript: unknown = DEP_ZERO

vi.mock('@/api/client', () => ({
  api: {
    get: vi.fn(async (path: string) => {
      if (path.includes('/deposits')) return { ok: true, data: depScript, watermark: 'w', nature: 'simulated' }
      return { ok: true, data: gateScript, watermark: 'w', nature: 'mixed' }
    }),
    post: vi.fn(async (path: string) => {
      if (path.endsWith('/deposits')) return { ok: true, data: { paid: true, amount_mou: 1, effective_mou: 1 }, watermark: 'w', nature: 'simulated' }
      if (path.includes('promotion-token')) return { ok: true, data: { issued: true, token_no: 'SPT-TEST000001AA', token_value: 'TDCA-PRT-testvalue0123456789', fingerprint_sha256_16: 'A1B2C3D4E5F60708' }, watermark: 'w', nature: 'real' }
      if (path.endsWith('/promotion')) return { ok: true, data: { promoted: true, promoted_at: '2026-10-23T08:00:00' }, watermark: 'w', nature: 'real' }
      if (path.includes('insurance-policies')) return { ok: true, data: { registered: true, policy_no: 'SIP-TEST0001', status: 'active' }, watermark: 'w', nature: 'real' }
      if (path.endsWith('/sandbox')) return { ok: true, data: { bound: true, result: 'passed' }, watermark: 'w', nature: 'real' }
      return { ok: false, reason: 'http_error' }
    }),
  },
  loadDraft: () => null,
  saveDraft: () => undefined,
  clearDraft: () => undefined,
}))

import { ChannelMyPage } from '@/pages/channel-my'

function renderPage() {
  return render(<ChannelMyPage />)
}

/** 最后一个结果面板（同 testid 多实例时取最新一步） */
function lastResult(): HTMLElement {
  const all = screen.getAllByTestId('step-result')
  return all[all.length - 1]
}

async function loadReg(demo: boolean) {
  fireEvent.change(screen.getByTestId('reg-input'), { target: { value: 'sar-test000001' } })
  if (demo) fireEvent.click(screen.getByTestId('demo-toggle'))
  fireEvent.click(screen.getByTestId('reg-load'))
  if (!demo) await screen.findByText(/已载入/)
}

describe('L1SI167-CHANNEL-UI-001 判成自测', () => {
  it('判成1（演示档）：一路点完四步，每步有可见结果，总状态条四格全 ✅', async () => {
    gateScript = GATE_FRESH
    depScript = DEP_ZERO
    renderPage()
    await loadReg(true)
    // 第 1 步
    fireEvent.click(screen.getByTestId('deposit-pay'))
    expect(lastResult()).toHaveTextContent('演示：已记账 1 MOU')
    expect(screen.getByTestId('progress-1')).toHaveTextContent('✅')
    // 第 2 步（四要件填齐）
    fireEvent.change(screen.getByTestId('tok-person'), { target: { value: 'founder' } })
    fireEvent.click(screen.getByText('填现在'))
    fireEvent.change(screen.getByTestId('tok-thing'), { target: { value: 'RUN-DEMO-1' } })
    fireEvent.change(screen.getByTestId('tok-intent'), { target: { value: '演示办转正' } })
    fireEvent.click(screen.getByTestId('token-issue'))
    expect(screen.getByTestId('token-once')).toHaveTextContent('TDCA-PRT-示例')
    expect(screen.getByTestId('token-once')).toHaveTextContent('此值只显示这一次')
    expect(screen.getByTestId('token-once')).toHaveTextContent('示例值')
    expect(screen.getByTestId('progress-2')).toHaveTextContent('✅')
    // 再点一次：令牌面板仍只有一个（只显一次）
    fireEvent.click(screen.getByTestId('token-issue'))
    expect(screen.getAllByTestId('token-once').length).toBe(1)
    // 第 3 步
    fireEvent.click(screen.getByTestId('promotion-run'))
    expect(lastResult()).toHaveTextContent('演示：已转正')
    expect(screen.getByTestId('progress-3')).toHaveTextContent('✅')
    // 第 4 步
    fireEvent.click(screen.getByTestId('sandbox-enter'))
    expect(lastResult()).toHaveTextContent('演示：沙盒验证已通过')
    expect(screen.getByTestId('progress-4')).toHaveTextContent('✅')
  })

  it('判成2（真跑档）：前置不满足时按钮置灰＋一句人话原因', async () => {
    gateScript = GATE_FRESH
    depScript = DEP_ZERO
    renderPage()
    // 未载号：四步全灰
    expect((screen.getByTestId('deposit-pay') as HTMLButtonElement).disabled).toBe(true)
    expect((screen.getByTestId('token-issue') as HTMLButtonElement).disabled).toBe(true)
    expect((screen.getByTestId('promotion-run') as HTMLButtonElement).disabled).toBe(true)
    expect((screen.getByTestId('sandbox-enter') as HTMLButtonElement).disabled).toBe(true)
    expect(screen.getByText('先在上面载入你的登记号')).toBeInTheDocument()
    // 载号后：新登记前置未达 → 第 2 步灰（沙盒未过）、第 4 步灰（押金不足），均有人话
    await loadReg(false)
    await screen.findByText(/沙盒验证还没通过/)
    expect((screen.getByTestId('token-issue') as HTMLButtonElement).disabled).toBe(true)
    expect(screen.getByText(/押金还不够/)).toBeInTheDocument()
    expect((screen.getByTestId('sandbox-enter') as HTMLButtonElement).disabled).toBe(true)
    // 第 1 步可点（真跑押付为记账口径）
    expect((screen.getByTestId('deposit-pay') as HTMLButtonElement).disabled).toBe(false)
  })

  it('判成2/3（真跑档·前置齐）：押付成功文案带「记账（模拟）·非实收」；转正后可见已转正', async () => {
    gateScript = GATE_READY
    depScript = { ...DEP_ZERO, effective_mou: 1, events: [{ event_no: 'SUD-T1', action: 'paid', amount_mou: 1, created_at: '2026-10-23T08:00:00' }] }
    renderPage()
    await loadReg(false)
    // 押金标示常显
    expect(screen.getByTestId('step-1')).toHaveTextContent('记账（模拟）· 非实收')
    // 第 4 步灯亮（有效 1 ≥ 门槛 1）——等后端实况回填
    await screen.findByText('当前有效额：1 MOU')
    expect((screen.getByTestId('sandbox-enter') as HTMLButtonElement).disabled).toBe(false)
    // 第 1 步真跑
    fireEvent.click(screen.getByTestId('deposit-pay'))
    expect((await screen.findByText(/已记账 1 MOU/)).textContent).toContain('已记账 1 MOU')
    // 第 2 步真跑（前置灯齐）
    expect((screen.getByTestId('token-issue') as HTMLButtonElement).disabled).toBe(true) // 四要件未填仍灰
    fireEvent.change(screen.getByTestId('tok-person'), { target: { value: 'founder' } })
    fireEvent.change(screen.getByTestId('tok-time'), { target: { value: '2026-10-23T08:00:00' } })
    fireEvent.change(screen.getByTestId('tok-thing'), { target: { value: 'RUN-TEST-1' } })
    fireEvent.change(screen.getByTestId('tok-intent'), { target: { value: '测试转正' } })
    expect((screen.getByTestId('token-issue') as HTMLButtonElement).disabled).toBe(false)
    fireEvent.click(screen.getByTestId('token-issue'))
    expect((await screen.findByTestId('token-once'))).toHaveTextContent('TDCA-PRT-testvalue0123456789')
    // 第 3 步真跑
    fireEvent.click(screen.getByTestId('promotion-run'))
    expect((await screen.findByText(/已转正 promoted_at＝/))).toHaveTextContent('已转正 promoted_at＝2026-10-23T08:00:00')
  })

  it('判成5：页面可见文案零内部编号（GSEQ-／TDCA-E-／NCA- 命中 0）', async () => {
    gateScript = GATE_FRESH
    depScript = DEP_ZERO
    renderPage()
    await loadReg(false)
    const page = screen.getByTestId('page-shell')
    expect(page.textContent ?? '').not.toMatch(/GSEQ-|TDCA-E-|NCA-/)
  })
})
