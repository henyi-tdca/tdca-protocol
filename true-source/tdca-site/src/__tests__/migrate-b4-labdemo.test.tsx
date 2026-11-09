// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: MIGRATE 批4（L1SI206）演练与实验两面迁入验证
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-MIGRATE-B4-001（演练与实验两面·场景数8不缩·仅人理由须写明）
// 验项：① /lab /demo 入 ROUTE_PATHS（PAGE_META 在册）；② 场景数 8 逐项在页（八枚场景筛钮）；
//   ③ 面额规则与锚四档逐字照旧（⛔改数⛔自造档名）；④ 两面演练标识明示（⛔读作真实交付）；
//   ⑤ 演练交互真跑（签到 +10／负余额拦截语逐字）
// =============================================================================
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { LabPage } from '@/pages/Lab'
import { DemoPage } from '@/pages/Demo'
import { ROUTE_PATHS, PAGE_META } from '@/pages/PagesIndex'

const SCENE8 = ['签到', '任务', '充值', '交付', '结算', '计税', '锚认证', '跨域引用'] as const

describe('MIGRATE 批4：/lab 与 /demo 入册与演练标识', () => {
  it('两面入 ROUTE_PATHS 且 PAGE_META 在册（20→22）', () => {
    expect(ROUTE_PATHS).toContain('/lab')
    expect(ROUTE_PATHS).toContain('/demo')
    expect(PAGE_META).toHaveLength(24) /* MIGRATE 批6：+2（/start /nca-guide） */
    const lab = PAGE_META.find((m) => m.path === '/lab')
    const demo = PAGE_META.find((m) => m.path === '/demo')
    expect(lab?.permission).toBe('公开')
    expect(demo?.permission).toBe('公开')
    // 两面 dataSource 皆自陈零接口零后端（纯前端页内状态）
    expect(lab?.dataSource).toContain('零接口调用、零后端写入')
    expect(demo?.dataSource).toContain('零接口调用、零后端写入')
  })

  it('/lab 场景数 8 逐项在页（⛔缩场景数）', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    for (const s of SCENE8) {
      expect(screen.getByTestId(`lab-filter-scene-${s}`)).toBeTruthy()
    }
  })

  it('/lab 面额规则与锚四档逐字照旧（照设计件 6146／TDCA-PUB-CORPUS-046）', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    const page = screen.getByTestId('lab-page')
    for (const t of [
      '签到 +10 积分／日（每日一次，断签不补）',
      '做任务 +20 积分／件（每日 4 件）',
      '充值面额 100／500／1000，支持自定义面额（发放路径，非改余额）',
      '演练完成 +50 积分／次（每日一次，三步走完才算；领取入口后续批次接入，本批只展示规则）',
      '模拟交付 −30 积分／件（剧本一 步 1 已开通）',
    ]) {
      expect(page.textContent).toContain(t)
    }
    for (const tier of ['固锚级', '移锚级', '记名级', '未达门槛']) {
      expect(page.textContent).toContain(tier)
    }
    // 税率必标示例比例（⛔真实税率）
    expect(page.textContent).toContain('示例比例')
    expect(page.textContent).toContain('⛔ 真实税率')
  })

  it('/lab 演练标识明示（页头横幅·非真实交易）', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    expect(screen.getByTestId('lab-banner').textContent).toContain('数据为模拟值')
    expect(screen.getByTestId('lab-banner').textContent).toContain('非真实交易')
  })

  it('/lab 演练交互真跑：签到 +10、负余额拦截语逐字', () => {
    render(<MemoryRouter><LabPage /></MemoryRouter>)
    const bal = () => screen.getByTestId('lab-balance').textContent
    // 初始余额按旧版口径（页内初始态，直接读页）
    fireEvent.click(screen.getByTestId('lab-checkin'))
    expect(bal()).toBe('10')
    // 余额 10 时模拟交付 −30 ⟹ 负余额拦截，提示语逐字
    fireEvent.click(screen.getByTestId('lab-s1-deliver'))
    expect(screen.getByTestId('lab-block-msg').textContent).toContain('积分不足，去签到或做任务')
    expect(bal()).toBe('10')
  })

  it('/demo 演示标识与两表在页（CREDIT_USES／DISCLAIMERS）', () => {
    render(<MemoryRouter><DemoPage /></MemoryRouter>)
    const page = screen.getByTestId('demo-page')
    expect(screen.getByTestId('demo-banner').textContent).toContain('数据为模拟值')
    expect(screen.getByTestId('demo-banner').textContent).toContain('非真实交易')
    for (const u of ['看公开资产', '用自助验链', '走三问向导']) {
      expect(page.textContent).toContain(u)
    }
    // 免责声明区非空（DISCLAIMERS 渲染）
    expect(page.textContent).toContain('演示')
  })
})
