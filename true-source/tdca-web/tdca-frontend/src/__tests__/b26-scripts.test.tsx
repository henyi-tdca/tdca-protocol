// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B26-后 三剧本测试（S1/S2/S3）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B26-003 §七验收九条——
//   S1 四步走通（−30/+120/−2.4/两单）／单据复制零下载／S2 三要素缺一过（具体原因）＋通过带三期换真根／
//   S3 哈希真算 64 位十六进制＋公域已验＋只显哈希与件名⛔内容／三段皆留流水八列齐／示例比例标
// =============================================================================
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'
import { LabPage } from '@/pages/lab'

const BLOCK_MSG = '积分不足，去签到或做任务'

describe('B26-后 S1：交付 → 结算 → 计税（一条直线）', () => {
  it('初始 0 点步 1 → 负余额拦截提示语逐字，余额不变', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('lab-s1-deliver'))
    expect(screen.getByTestId('lab-block-msg').textContent).toBe(BLOCK_MSG)
    expect(screen.getByTestId('lab-balance').textContent).toBe('0')
    expect(screen.queryByTestId('lab-s1-receipts')).toBeNull()
  })

  it('四步走完：100 → 70 → 190 → 187.6，两单可出可复（不触发文件下载）', () => {
    let copied = ''
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: (t: string) => { copied = t; return Promise.resolve() } },
    })
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('lab-topup-100'))
    fireEvent.click(screen.getByTestId('lab-s1-deliver'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('70')
    fireEvent.click(screen.getByTestId('lab-s1-settle'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('190')
    fireEvent.click(screen.getByTestId('lab-s1-tax'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('187.6')
    fireEvent.click(screen.getByTestId('lab-s1-issue'))
    const settle = screen.getByTestId('lab-s1-receipt-结算单').textContent ?? ''
    const tax = screen.getByTestId('lab-s1-receipt-税单').textContent ?? ''
    expect(settle).toContain('SIM-ORD-0001')
    expect(settle).toContain('环销结算额 120 积分')
    expect(tax).toContain('SIM-ORD-0002')
    expect(tax).toContain('税额 2.4 积分')
    expect(tax).toContain('示例比例 2%')
    expect(tax).toContain('⛔ 真实税率')
    // 单号可回查：两单仍在页内
    expect(screen.getByTestId('lab-s1-receipts').textContent).toContain('SIM-ORD-0001')
    expect(screen.getByTestId('lab-s1-receipts').textContent).toContain('SIM-ORD-0002')
    // 复制为文本，不触发文件下载
    fireEvent.click(screen.getByTestId('lab-s1-copy-结算单'))
    expect(copied).toContain('SIM-ORD-0001')
    expect(screen.getByTestId('lab-s1-copy-note').textContent).toContain('不触发文件下载')
    // 流水八列齐：交付 −30／结算 +120／计税 −2.4 皆入表
    const table = screen.getByTestId('lab-ledger-table').textContent ?? ''
    expect(table).toContain('SIM-FLOW-0002') // 交付 −30
    expect(screen.getByTestId('lab-flow-SIM-FLOW-0002').textContent).toContain('−30')
    expect(screen.getByTestId('lab-flow-SIM-FLOW-0003').textContent).toContain('+120')
    expect(screen.getByTestId('lab-flow-SIM-FLOW-0004').textContent).toContain('−2.4')
    expect(table).toContain('SIM-NCA-0004（模拟）')
    expect(table).toContain('SIM-RUN-0001')
  })
})

describe('B26-后 S2：模拟锚认证（四档＋三要素，必须能不通过）', () => {
  it('三要素齐 → 模拟通过＋三期换真根；缺见证 → 模拟不通过＋缺见证要素（原因原文）', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('lab-topup-100'))
    fireEvent.click(screen.getByTestId('lab-s2-tier-固锚级'))
    expect(screen.getByTestId('lab-s2-tier-desc').textContent).toContain('设备唯一且物理地址保持')
    // 通过路径
    fireEvent.click(screen.getByTestId('lab-s2-run'))
    expect(screen.getByTestId('lab-balance').textContent).toBe('80')
    expect(screen.getByTestId('lab-s2-records').textContent).toContain('模拟通过')
    expect(screen.getByTestId('lab-s2-records').textContent).toContain('三期换真根')
    expect(screen.getByTestId('lab-s2-records').textContent).toContain('SIMULATED')
    // 不通过路径：缺见证要素
    fireEvent.click(screen.getByTestId('lab-s2-elem-witness'))
    fireEvent.click(screen.getByTestId('lab-s2-run'))
    expect(screen.getByTestId('lab-s2-records').textContent).toContain('模拟不通过')
    expect(screen.getByTestId('lab-s2-records').textContent).toContain('缺见证要素')
  })

  it('未选等级 → 提示先选，余额不动', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('lab-topup-100'))
    fireEvent.click(screen.getByTestId('lab-s2-run'))
    expect(screen.getByTestId('lab-block-msg').textContent).toContain('请先选择锚等级')
    expect(screen.getByTestId('lab-balance').textContent).toBe('100')
  })
})

describe('B26-后 S3：跨域引用（哈希真算）', () => {
  it('生成 NCA：SHA-256 真算 64 位十六进制（对得上已知值）；公域只验哈希不搬内容；验后出已验', async () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.change(screen.getByTestId('lab-s3-content'), { target: { value: 'abc' } })
    fireEvent.click(screen.getByTestId('lab-s3-generate'))
    // SHA-256('abc') 已知值 —— 真算非写死假串之证
    const expected = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    await waitFor(() => {
      expect(screen.getByTestId('lab-s3-hash').textContent).toContain(expected)
    })
    expect(screen.getByTestId('lab-s3-link').textContent).toContain('SIM-LINK-0001')
    // 公域侧只显哈希与件名，⛔ 显示内容
    const pub = screen.getByTestId('lab-s3-public').textContent ?? ''
    expect(pub).not.toContain('abc')
    expect(pub).toContain('示例件 A')
    expect(pub).toContain('待公域验哈希')
    // 交公域验 → 已验（真比对）
    fireEvent.click(screen.getByTestId('lab-s3-verify'))
    await waitFor(() => {
      expect(screen.getByTestId('lab-s3-verdict').textContent).toContain('已验')
    })
    expect(screen.getByTestId('lab-s3-verdict').textContent).toContain('两域互认')
    // 留痕：跨域引用 0 额流水入表
    expect(screen.getByTestId('lab-ledger-table').textContent).toContain('跨域引用')
  })
})

describe('B26-后 硬约束守护（DOM 级）', () => {
  it('剧本区零金额字样＋示例比例标＋会话句＋零内部编号；交互后 localStorage 零写入', () => {
    const spy = Object.getOwnPropertyDescriptor(Storage.prototype, 'setItem')
    let wrote = false
    Object.defineProperty(Storage.prototype, 'setItem', {
      configurable: true,
      value: () => { wrote = true },
    })
    const { container } = render(<MemoryRouter><LabPage /></MemoryRouter>)
    fireEvent.click(screen.getByTestId('lab-topup-100'))
    fireEvent.click(screen.getByTestId('lab-s1-deliver'))
    fireEvent.click(screen.getByTestId('lab-s2-tier-移锚级'))
    fireEvent.click(screen.getByTestId('lab-s2-run'))
    fireEvent.click(screen.getByTestId('lab-s3-generate'))
    const text = container.textContent ?? ''
    for (const bad of ['¥', '￥', '元', '价格', '档位', '付费', 'EIOS-', 'EVT-']) {
      expect(text.includes(bad)).toBe(false)
    }
    expect(text.match(/(^|[^A-Za-z])([PAMS]-?\d)/g) ?? []).toEqual([])
    expect(text).toContain('示例比例 2%，⛔ 真实税率')
    expect(text).toContain('本演示为单次会话，刷新即清空；不是你的资产，也不会保存')
    expect(text).toContain('档名以在册为准')
    if (spy) Object.defineProperty(Storage.prototype, 'setItem', spy)
    expect(wrote).toBe(false)
  })
})
