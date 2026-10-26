// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B25 演示页测试（一页四块模拟）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B25-001 §五验收七条——
//   页头模拟标识／四块齐各带 SIMULATED／两个跑一次按钮有结果／免责三条逐字／
//   零金额字样（¥／￥／元／价格／档位／付费）＋零内部编号／纯页内状态
// =============================================================================
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'
import { DemoPage } from '@/pages/demo'
import { PAGE_COMPONENTS, ROUTE_PATHS } from '@/pages/pages'

describe('L1SI175-B25 路由注册', () => {
  it('/demo 入 ROUTE_PATHS 且组件映射齐', () => {
    expect(ROUTE_PATHS).toContain('/demo')
    expect(PAGE_COMPONENTS['/demo']).toBeTruthy()
  })
})

describe('B25 演示页：三处模拟标识与四块齐', () => {
  it('页头醒目句在（三处之一）', () => {
    render(<MemoryRouter><DemoPage /></MemoryRouter>)
    expect(screen.getByTestId('demo-banner').textContent).toContain('演示区 · 数据为模拟值 · 非真实交易')
  })

  it('四块齐，各带 SIMULATED 标（三处之二）', () => {
    render(<MemoryRouter><DemoPage /></MemoryRouter>)
    const text = document.body.textContent ?? ''
    for (const tid of ['demo-credits', 'demo-wallet', 'demo-settlement', 'demo-tax']) {
      expect(screen.getByTestId(tid)).toBeTruthy()
    }
    // 每块一个 SIMULATED 角标（页头另有 PageShell 自带 1 个，共 5）
    expect(screen.getAllByTestId('simulated-badge').length).toBe(5)
    for (const tid of ['demo-credits', 'demo-wallet', 'demo-settlement', 'demo-tax']) {
      expect(screen.getByTestId(tid).querySelector('[data-testid="simulated-badge"]')).not.toBeNull()
    }
    expect(text).toContain('剩余积分')
    expect(text).toContain('1,200')
    expect(text).toContain('不换钱、不可提现')
    expect(text).toContain('现金余额')
    expect(text).toContain('三期开放')
    // 环销/净额/定向支付/基数/应缴/留痕 为按钮触发的结果区，在下方按钮用例断言
  })

  it('两个跑一次按钮可点且有结果（结算三步／计税三步）', () => {
    render(<MemoryRouter><DemoPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('demo-run-settlement'))
    const s = screen.getByTestId('settlement-result').textContent ?? ''
    expect(s).toContain('① 环销')
    expect(s).toContain('② 净额')
    expect(s).toContain('③ 定向支付')
    expect(s).toContain('300')
    expect(s).toContain('120')
    expect(s).toContain('80')
    expect(s).toContain('沙盒模拟，不涉及任何真实资金')
    fireEvent.click(screen.getByTestId('demo-run-tax'))
    const t = screen.getByTestId('tax-result').textContent ?? ''
    expect(t).toContain('① 基数：模拟交易额 500 积分')
    expect(t).toContain('② 应缴：示例比例 2% → 10 积分')
    expect(t).toContain('③ 留痕：')
    expect(t).toContain('模拟存证号')
    expect(t).toContain('真实税务与票据在三期')
  })

  it('免责三条逐字在（三处之三）', () => {
    render(<MemoryRouter><DemoPage /></MemoryRouter>)
    const foot = screen.getByTestId('demo-disclaimers').textContent ?? ''
    expect(foot).toContain('本页所有数字为模拟值，不是你的真实资产，⛔ 可提现 / ⛔ 可交易。')
    expect(foot).toContain('体验期站内功能免费；演示值不代表将来定价，也不算报价。')
    expect(foot).toContain('真实钱包 / 充值 / 结算 / 税收 / 税务票据 均在三期实现，届时另立制度。')
  })
})

describe('B25 演示页：零金额零编号（DOM 级）', () => {
  it('全页渲染文本禁样全零（¥/￥/元/价格/档位/付费/EIOS-/EVT-/族编号）', () => {
    const { container } = render(<MemoryRouter><DemoPage /></MemoryRouter>)
    const text = container.textContent ?? ''
    for (const bad of ['¥', '￥', '元', '价格', '档位', '付费', 'EIOS-', 'EVT-']) {
      expect(text.includes(bad)).toBe(false)
    }
    expect(text.match(/(^|[^A-Za-z])([PAMS]-?\d)/g) ?? []).toEqual([])
  })

  it('零后端零本地存：页内无 localStorage 写入', () => {
    const spy = Object.getOwnPropertyDescriptor(Storage.prototype, 'setItem')
    let wrote = false
    Object.defineProperty(Storage.prototype, 'setItem', {
      configurable: true,
      value: () => { wrote = true },
    })
    render(<MemoryRouter><DemoPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('demo-run-settlement'))
    fireEvent.click(screen.getByTestId('demo-run-tax'))
    if (spy) Object.defineProperty(Storage.prototype, 'setItem', spy)
    expect(wrote).toBe(false)
  })
})
