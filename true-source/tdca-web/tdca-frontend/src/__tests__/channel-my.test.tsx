// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-CHANNEL-MY-001 | 目标函数: L1SI167-CHANNEL-UI-001 判成自测
// 约束矩阵: 判成五条（四步走完每步可见／置灰+人话／物自动带出只读／令牌只显一次／零内部编号）
//           ＋ 步序修正令（-002）：押金⟹过闸(审查+沙盒)⟹令牌⟹转正
// 说明: mock 掉 api 客户端（不走真网络）；演示档与真跑档两路各验
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
const DEP_ONE = { ...DEP_ZERO, effective_mou: 1, events: [{ event_no: 'SUD-T1', action: 'paid', amount_mou: 1, created_at: '2026-10-23T08:00:00' }] }

let gateScript: unknown = GATE_FRESH
let depScript: unknown = DEP_ZERO

vi.mock('@/api/client', () => ({
  api: {
    get: vi.fn(async (path: string) => {
      if (path.includes('/auth/me')) return { ok: true, data: { username: 'founder' }, watermark: 'w', nature: 'real' }
      if (path.includes('/deposits')) return { ok: true, data: depScript, watermark: 'w', nature: 'simulated' }
      return { ok: true, data: gateScript, watermark: 'w', nature: 'mixed' }
    }),
    post: vi.fn(async (path: string) => {
      if (path.endsWith('/ns-review')) return { ok: true, data: { reviewed: true, result: 'passed' }, watermark: 'w', nature: 'real' }
      if (path.endsWith('/sandbox')) {
        gateScript = GATE_READY
        return { ok: true, data: { bound: true, result: 'passed' }, watermark: 'w', nature: 'real' }
      }
      if (path.endsWith('/deposits')) return { ok: true, data: { paid: true, amount_mou: 1, effective_mou: 1 }, watermark: 'w', nature: 'simulated' }
      if (path.includes('promotion-token')) return { ok: true, data: { issued: true, token_no: 'SPT-TEST000001AA', token_value: 'TDCA-PRT-testvalue0123456789', fingerprint_sha256_16: 'A1B2C3D4E5F60708' }, watermark: 'w', nature: 'real' }
      if (path.endsWith('/promotion')) return { ok: true, data: { promoted: true, promoted_at: '2026-10-23T08:00:00' }, watermark: 'w', nature: 'real' }
      if (path.includes('insurance-policies')) return { ok: true, data: { registered: true, policy_no: 'SIP-TEST0001', status: 'active' }, watermark: 'w', nature: 'real' }
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

/** 最后一个结果面板（同 testid 多实例时取最新一处） */
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

describe('L1SI167-CHANNEL-UI-001（-002 步序修正）判成自测', () => {
  it('判成1（演示档·走查脚本甲）：押金⟹过闸⟹令牌⟹转正，每步有可见结果，四格全 ✅', async () => {
    gateScript = GATE_FRESH
    depScript = DEP_ZERO
    renderPage()
    await loadReg(true)
    // 第 1 步：交押金
    fireEvent.click(screen.getByTestId('deposit-pay'))
    expect(lastResult()).toHaveTextContent('演示：已记账 1 MOU')
    expect(screen.getByTestId('step-1')).toHaveTextContent('记账（模拟）· 非实收')
    expect(screen.getByTestId('progress-1')).toHaveTextContent('✅')
    // 第 2 步：过闸两灯先红后绿（演示模式按钮可直接点）
    expect(screen.getByTestId('step-2')).toHaveTextContent('⛔ 合规审查已通过')
    fireEvent.click(screen.getByTestId('review-submit'))
    expect(lastResult()).toHaveTextContent('演示：合规审查已通过')
    fireEvent.click(screen.getByTestId('sandbox-enter'))
    expect(lastResult()).toHaveTextContent('演示：沙盒验证已通过')
    expect(screen.getByTestId('progress-2')).toHaveTextContent('✅')
    // 第 3 步：物自动带出、灰显；令牌只显一次
    expect(screen.getByTestId('tok-thing')).toHaveValue('物：RUN-DEMO-0001（第 2 步沙盒运行号，自动带出）')
    fireEvent.click(screen.getByText('填现在'))
    fireEvent.change(screen.getByTestId('tok-intent'), { target: { value: '演示办转正' } })
    fireEvent.click(screen.getByTestId('token-issue'))
    expect(screen.getByTestId('token-once')).toHaveTextContent('TDCA-PRT-示例')
    expect(screen.getByTestId('token-once')).toHaveTextContent('此值只显示这一次')
    expect(screen.getByTestId('token-once')).toHaveTextContent('示例值')
    expect(screen.getByTestId('progress-3')).toHaveTextContent('✅')
    fireEvent.click(screen.getByTestId('token-issue'))
    expect(screen.getAllByTestId('token-once').length).toBe(1)
    // 第 4 步：办转正
    fireEvent.click(screen.getByTestId('promotion-run'))
    expect(lastResult()).toHaveTextContent('演示：已转正')
    expect(screen.getByTestId('progress-4')).toHaveTextContent('✅')
  })

  it('判成2（真跑档·新登记）：审查三引用未填灰+人话；押金不足进不了沙盒；令牌两灯未绿不可签', async () => {
    gateScript = GATE_FRESH
    depScript = DEP_ZERO
    renderPage()
    // 未载号：四步全灰
    expect(screen.getByTestId('deposit-pay')).toBeDisabled()
    expect(screen.getByTestId('review-submit')).toBeDisabled()
    expect(screen.getByTestId('sandbox-enter')).toBeDisabled()
    expect(screen.getByTestId('token-issue')).toBeDisabled()
    expect(screen.getByText('先在上面载入你的登记号')).toBeInTheDocument()
    await loadReg(false)
    // 审查：三引用未填 → 灰 + 人话
    await screen.findByText(/审查三引用（边界声明／对抗集／场景范围）填齐再提交/)
    expect(screen.getByTestId('review-submit')).toBeDisabled()
    // 沙盒：押金不足 → 灰 + 人话
    expect(screen.getByTestId('sandbox-enter')).toBeDisabled()
    expect(screen.getByText(/押金还不够/)).toBeInTheDocument()
    // 令牌：合规审查未过 → 灰 + 人话
    expect(screen.getByTestId('token-issue')).toBeDisabled()
    expect(screen.getByText(/合规审查还没通过/)).toBeInTheDocument()
  })

  it('判成2/3（真跑档·前置齐）：审查提交→沙盒进→物带出→令牌一次→办转正全链', async () => {
    gateScript = GATE_FRESH
    depScript = DEP_ONE
    renderPage()
    await loadReg(false)
    await screen.findByText('当前有效额：1 MOU')
    // 过闸 A：提交审查（三引用填齐）
    fireEvent.change(screen.getByTestId('ns-boundary'), { target: { value: 'BND-1' } })
    fireEvent.change(screen.getByTestId('ns-adversarial'), { target: { value: 'ADV-1' } })
    fireEvent.change(screen.getByTestId('ns-scope'), { target: { value: 'SCN-1' } })
    expect(screen.getByTestId('review-submit')).toBeEnabled()
    fireEvent.click(screen.getByTestId('review-submit'))
    expect((await screen.findByText('合规审查已通过'))).toBeInTheDocument()
    // 过闸 B：进沙盒（运行号+SEA 填齐）
    fireEvent.change(screen.getByTestId('sb-sea'), { target: { value: 'SEA-1' } })
    fireEvent.change(screen.getByTestId('sb-run'), { target: { value: 'RUN-REAL-1' } })
    expect(screen.getByTestId('sandbox-enter')).toBeEnabled()
    fireEvent.click(screen.getByTestId('sandbox-enter'))
    expect((await screen.findByText(/沙盒验证已通过（运行号 RUN-REAL-1）/))).toBeInTheDocument()
    // 第 3 步：物自动带出（只读值含运行号）；人自动带出本会话
    expect(screen.getByTestId('tok-thing')).toHaveValue('物：RUN-REAL-1（第 2 步沙盒运行号，自动带出）')
    expect(screen.getByTestId('tok-person')).toHaveValue('founder（本会话，自动带出）')
    fireEvent.click(screen.getByText('填现在'))
    fireEvent.change(screen.getByTestId('tok-intent'), { target: { value: '正式转正' } })
    expect(screen.getByTestId('token-issue')).toBeEnabled()
    fireEvent.click(screen.getByTestId('token-issue'))
    expect((await screen.findByTestId('token-once'))).toHaveTextContent('TDCA-PRT-testvalue0123456789')
    // 第 4 步：办转正
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
