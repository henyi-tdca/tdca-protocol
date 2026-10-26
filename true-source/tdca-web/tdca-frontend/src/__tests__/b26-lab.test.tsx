// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B26 模拟演练区测试（五卡＋流水表）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B26-001 §八回报七项——
//   会话限制句／五卡齐各带 SIMULATED 与必带文案五句逐字／签到+10 每日一次／任务 20×4 上限／
//   充值发放路径／负余额拦截实证（提示语逐字「积分不足，去签到或做任务」）／计税免费＋示例比例标／
//   流水八字段一笔全值＋筛选＋导出复制／零金额字样＋零 localStorage＋零内部编号
// =============================================================================
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'
import { DemoPage } from '@/pages/demo'
import { LabPage } from '@/pages/lab'
import { PAGE_COMPONENTS, ROUTE_PATHS } from '@/pages/pages'

const BLOCK_MSG = '积分不足，去签到或做任务'

describe('L1SI175-B26 路由注册', () => {
  it('/lab 入 ROUTE_PATHS 且组件映射齐；/demo 页尾一句一链在', () => {
    expect(ROUTE_PATHS).toContain('/lab')
    expect(PAGE_COMPONENTS['/lab']).toBeTruthy()
    render(<MemoryRouter><DemoPage /></MemoryRouter>)
    const link = screen.getByTestId('demo-b2-lab')
    expect(link.textContent).toContain('想动手走一遍')
    expect(link.textContent).toContain('模拟演练区')
    expect(link.querySelector('a')?.getAttribute('href')).toBe('/lab')
  })
})

describe('B26 演练区：页头会话限制句与五卡齐', () => {
  it('页头句与会话限制句在（显眼处）', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    expect(screen.getByTestId('lab-banner').textContent).toContain('演练区 · 数据为模拟值 · 非真实交易')
    expect(screen.getByTestId('lab-session').textContent).toContain('本演示为单次会话，刷新即清空；不是你的资产，也不会保存')
  })

  it('五卡齐，各带 SIMULATED 角标；必带文案五句逐字', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    for (const tid of ['lab-wallet', 'lab-topup', 'lab-settle', 'lab-tax', 'lab-anchor']) {
      const el = screen.getByTestId(tid)
      expect(el).toBeTruthy()
      expect(el.querySelector('[data-testid="simulated-badge"]')).not.toBeNull()
      expect(el.textContent).toContain('演示，不涉真实资金与真实税')
      expect(el.textContent).toContain('流水号：')
    }
    // PageShell 1 ＋五卡 5＋规则表 1＋流水表 1＋选剧本区 1（三剧本子区不带独立角标）
    expect(screen.getAllByTestId('simulated-badge').length).toBe(9)
    const text = document.body.textContent ?? ''
    expect(text).toContain('演示钱包：站内虚拟积分，不可提现、不可转让、不可兑人民币')
    expect(text).toContain('模拟充值：点击即加积分，不发生任何真实支付')
    expect(text).toContain('模拟结算：仅演示算法与流程，无真实资金流转')
    expect(text).toContain('模拟计税：按在册税率演算，不作任何申报依据')
    expect(text).toContain('模拟认证：物理根为三期，演示不签发真证书')
    // 空态句逐字
    expect(text).toContain('还没有流水 —— 先签到，或点开任意一卡试一次')
  })
})

describe('B26 演练区：发放入口（签到／任务／充值）', () => {
  it('签到 +10，每日一次拦截', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('lab-checkin'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('10')
    fireEvent.click(screen.getByTestId('lab-checkin'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('10')
    expect(screen.getByTestId('lab-block-msg').textContent).toContain('今日已签到')
  })

  it('做任务 +20／件，每日 4 件上限', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    for (let i = 0; i < 4; i++) fireEvent.click(screen.getByTestId('lab-task'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('80')
    fireEvent.click(screen.getByTestId('lab-task'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('80')
    expect(screen.getByTestId('lab-block-msg').textContent).toContain('每日 4 件')
  })

  it('充值为发放路径：面额按钮与自定义面额均加积分；自定义标明模拟', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('lab-topup-100'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('100')
    fireEvent.change(screen.getByTestId('lab-topup-custom'), { target: { value: '50' } })
    fireEvent.click(screen.getByTestId('lab-topup-custom-go'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('150')
    const text = screen.getByTestId('lab-topup').textContent ?? ''
    expect(text).toContain('自定义面额（模拟）')
    expect(text).toContain('⛔ 改余额输入框')
  })
})

describe('B26 演练区：负余额拦截实证（本批唯一活消耗路径 −20／次）', () => {
  it('初始 0 点锚认证 → 提示语逐字且余额不变；充值 +100 再点 → −20 成功出认证记录', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    // ① 初始余额 0 < 20：拦下
    fireEvent.click(screen.getByTestId('lab-anchor-run'))
    expect(screen.getByTestId('lab-block-msg').textContent).toBe(BLOCK_MSG)
    expect(screen.getByTestId('lab-balance').textContent).toBe('0')
    expect(screen.queryByTestId('lab-anchor-records')).toBeNull()
    // ② 充值 +100 凑够
    fireEvent.click(screen.getByTestId('lab-topup-100'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('100')
    // ③ 再点：−20 成功，出认证记录
    fireEvent.click(screen.getByTestId('lab-anchor-run'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('80')
    expect(screen.getByTestId('lab-anchor-records').textContent).toContain('模拟锚认证通过')
    expect(screen.getByTestId('lab-anchor-records').textContent).toContain('演示不签发真证书')
    // ④ 拦下不产生流水（账本只有充值＋锚认证两笔，无空额流水）
    const rows = screen.getAllByTestId(/^lab-flow-/)
    expect(rows).toHaveLength(2)
    expect(rows[0].textContent).toContain('锚认证')
    expect(rows[0].textContent).toContain('−20')
    expect(rows[1].textContent).toContain('充值')
  })
})

describe('B26 演练区：结算本批不扣款／计税免费', () => {
  it('结算走流程不扣款（如实标注后批）；计税免费试算不扣＋示例比例标', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('lab-topup-100'))
    fireEvent.click(screen.getByTestId('lab-settle-run'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('100')
    expect(screen.getByTestId('lab-settle-note').textContent).toContain('剧本一')
    fireEvent.change(screen.getByTestId('lab-tax-base'), { target: { value: '200' } })
    fireEvent.click(screen.getByTestId('lab-tax-run'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('100')
    const taxText = screen.getByTestId('lab-tax').textContent ?? ''
    expect(taxText).toContain('示例比例，⛔ 真实税率')
    expect(screen.getByTestId('lab-tax-result').textContent).toContain('试算额 4 积分')
    expect(screen.getByTestId('lab-tax-result').textContent).toContain('不额外扣')
  })
})

describe('B26 演练区：流水表八字段全值＋筛选＋导出复制', () => {
  it('一笔流水八字段全值（流水号／+08 时点／类型／场景／变动值／变动后余额／SIM-NCA／SIM-RUN）', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('lab-checkin'))
    const row = screen.getByTestId('lab-flow-SIM-FLOW-0001').textContent ?? ''
    expect(row).toContain('SIM-FLOW-0001')
    expect(row).toMatch(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \+08/)
    expect(row).toContain('发放')
    expect(row).toContain('签到')
    expect(row).toContain('+10')
    expect(row).toContain('10') // 变动后余额
    expect(row).toContain('SIM-NCA-0001（模拟）')
    expect(row).toContain('SIM-RUN-0001')
  })

  it('按类型／场景筛选生效；导出＝复制为文本（不动文件下载）', async () => {
    let copied = ''
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: (t: string) => { copied = t; return Promise.resolve() } },
    })
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('lab-checkin')) // 发放·签到
    fireEvent.click(screen.getByTestId('lab-topup-100')) // 发放·充值
    fireEvent.click(screen.getByTestId('lab-anchor-run')) // 消耗·锚认证 −20
    // 类型筛选：只看消耗
    fireEvent.click(screen.getByTestId('lab-filter-type-消耗'))
    let rows = screen.getAllByTestId(/^lab-flow-/)
    expect(rows).toHaveLength(1)
    expect(rows[0].textContent).toContain('锚认证')
    expect(rows[0].textContent).toContain('−20')
    // 场景筛选：全部类型 + 只看充值
    fireEvent.click(screen.getByTestId('lab-filter-type-全部'))
    fireEvent.click(screen.getByTestId('lab-filter-scene-充值'))
    rows = screen.getAllByTestId(/^lab-flow-/)
    expect(rows).toHaveLength(1)
    expect(rows[0].textContent).toContain('充值')
    // 导出复制
    fireEvent.click(screen.getByTestId('lab-filter-scene-全部'))
    fireEvent.click(screen.getByTestId('lab-export'))
    expect(copied).toContain('SIM-FLOW-0001')
    expect(copied.split('\n')).toHaveLength(3)
    expect(screen.getByTestId('lab-export-note').textContent).toContain('已复制 3 行流水')
    expect(screen.getByTestId('lab-export-note').textContent).toContain('不触发文件下载')
  })
})

describe('B26 演练区：零金额零编号零持久化（DOM 级）', () => {
  it('全页禁样全零（¥/￥/元/价格/档位/付费/EIOS-/EVT-/族编号）；交互后 localStorage 零写入', () => {
    const spy = Object.getOwnPropertyDescriptor(Storage.prototype, 'setItem')
    let wrote = false
    Object.defineProperty(Storage.prototype, 'setItem', {
      configurable: true,
      value: () => { wrote = true },
    })
    const { container } = render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('lab-checkin'))
    fireEvent.click(screen.getByTestId('lab-topup-100'))
    fireEvent.click(screen.getByTestId('lab-anchor-run'))
    fireEvent.change(screen.getByTestId('lab-tax-base'), { target: { value: '200' } })
    fireEvent.click(screen.getByTestId('lab-tax-run'))
    fireEvent.click(screen.getByTestId('lab-export'))
    const text = container.textContent ?? ''
    for (const bad of ['¥', '￥', '元', '价格', '档位', '付费', 'EIOS-', 'EVT-']) {
      expect(text.includes(bad)).toBe(false)
    }
    expect(text.match(/(^|[^A-Za-z])([PAMS]-?\d)/g) ?? []).toEqual([])
    if (spy) Object.defineProperty(Storage.prototype, 'setItem', spy)
    expect(wrote).toBe(false)
  })
})
