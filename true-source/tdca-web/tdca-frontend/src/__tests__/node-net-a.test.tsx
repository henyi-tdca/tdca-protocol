// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: NODE-NET-A-001 私域两卡＋公域四块自测
// 约束矩阵: 十条硬约束自测——真节点恰 1 个（⛔ 演示点）、零「实时」字样、九类接口齐、
//   未实现一律「建设中 · 未开放」唯文档/协议包分发可用、状态栏「数据截至 HH:MM」在、
//   私域七字段无真值如实「未设置／待复算」、卡底固定句原文、三处同源（唯一数据模块）
// =============================================================================
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'
import { MeNodeNetPage } from '@/pages/me-node-net'
import { NodeNetPage } from '@/pages/node-net'
import { NINE_APIS, NODES, NODE_REGULATION } from '@/pages/node-net-data'
import { PAGE_COMPONENTS, ROUTE_PATHS } from '@/pages/pages'

describe('NODE-NET-A-001 路由注册', () => {
  it('/me/node/net 与 /nodes 入 ROUTE_PATHS 且组件映射齐', () => {
    expect(ROUTE_PATHS).toContain('/me/node/net')
    expect(ROUTE_PATHS).toContain('/nodes')
    expect(PAGE_COMPONENTS['/me/node/net']).toBeTruthy()
    expect(PAGE_COMPONENTS['/nodes']).toBeTruthy()
  })
})

describe('公域四块：可视图 / 状态栏 / 接口信息 / 条例入口', () => {
  it('可视图只画已披露真节点——恰 1 个，空位固定句（⛔ 演示点）', () => {
    render(<MemoryRouter><NodeNetPage /></MemoryRouter>)
    expect(screen.getAllByTestId('nn-viz-node')).toHaveLength(1)
    expect(NODES).toHaveLength(1)
    expect(screen.getAllByTestId('nn-viz-empty').length).toBeGreaterThan(0)
    const emptyTexts = screen.getAllByTestId('nn-viz-empty').map((e) => e.textContent ?? '')
    for (const t of emptyTexts) expect(t).toContain('建设中 · 尚无其他节点接入')
  })

  it('图例含四态与两种连线', () => {
    render(<MemoryRouter><NodeNetPage /></MemoryRouter>)
    const states = screen.getAllByTestId('nn-legend-state').map((e) => e.textContent)
    expect(states).toEqual(['已适配', '待适配', '冲突·不可启用', '父级直承'])
    const links = screen.getAllByTestId('nn-legend-link').map((e) => e.textContent)
    expect(links).toEqual(['制度同构', '未适配'])
  })

  it('状态栏：数据截至 HH:MM、一节点一行、无心跳固定句、零「实时」字样', () => {
    render(<MemoryRouter><NodeNetPage /></MemoryRouter>)
    const stamp = screen.getByTestId('nn-status-stamp').textContent ?? ''
    expect(stamp).toMatch(/数据截至 \d{2}:\d{2}/)
    expect(screen.getAllByTestId('nn-status-row')).toHaveLength(1)
    const row = screen.getByTestId('nn-status-row').textContent ?? ''
    expect(row).toContain('尚无心跳 · 待节点首次上报')
    expect(row).toContain('待复算')
    expect(row).toContain('V1.0')
    // 全页零「实时」
    expect(screen.getByTestId('node-net-page').textContent).not.toContain('实时')
  })

  it('接口九类逐行：唯「文档／协议包分发」可用，余皆「建设中 · 未开放」', () => {
    render(<MemoryRouter><NodeNetPage /></MemoryRouter>)
    const rows = screen.getAllByTestId('nn-api-row')
    expect(rows).toHaveLength(9)
    expect(NINE_APIS).toHaveLength(9)
    for (const r of rows) {
      const t = r.textContent ?? ''
      if (t.includes('文档／协议包分发')) expect(t).toContain('可用')
      else expect(t).toContain('建设中 · 未开放')
    }
  })

  it('条例入口：固定抬头＋三处互链条号', () => {
    render(<MemoryRouter><NodeNetPage /></MemoryRouter>)
    const reg = screen.getByTestId('nn-reg').textContent ?? ''
    expect(reg).toContain('制度随场景层级向下细化')
    expect(reg).toContain('子级须向其上一层适配')
    expect(reg).toContain('第 16 条')
    expect(reg).toContain('第 10 条')
    expect(reg).toContain('第 12 条')
    expect(reg).toContain(NODE_REGULATION.version)
  })
})

describe('私域两卡：我的节点 / 条例与契约', () => {
  it('卡一七字段无真值如实标（未设置／待复算）＋卡底固定句', () => {
    render(<MemoryRouter><MeNodeNetPage /></MemoryRouter>)
    const card1 = screen.getByTestId('mn-card1').textContent ?? ''
    expect(card1).toContain('未设置')
    expect(card1).toContain('待复算')
    expect(card1).toContain('本节点为分层最低层场景；制度不减项、门槛不降低。')
  })

  it('卡二条例真值＋九类清单＋契约版本＋变更公告暂无', () => {
    render(<MemoryRouter><MeNodeNetPage /></MemoryRouter>)
    const card2 = screen.getByTestId('mn-card2').textContent ?? ''
    expect(card2).toContain('业务端节点接入与同构契约条例')
    expect(card2).toContain('已生效')
    expect(screen.getAllByTestId('mn-api-chip')).toHaveLength(9)
    expect(card2).toContain('变更公告')
    expect(card2).toContain('暂无')
  })

  it('下载两链指向 /docs/regulation 在册件名', () => {
    render(<MemoryRouter><MeNodeNetPage /></MemoryRouter>)
    expect(screen.getByTestId('mn-reg-human').getAttribute('href')).toContain('/docs/regulation/')
    expect(screen.getByTestId('mn-reg-machine').getAttribute('href')).toContain('COMPILED')
  })
})

describe('三处同源（硬约束八）', () => {
  it('私域卡与公域状态栏读同一数据模块', () => {
    render(<MemoryRouter><><MeNodeNetPage /><NodeNetPage /></></MemoryRouter>)
    const statusRow = within(screen.getAllByTestId('nn-status-row')[0]).getByText('创世节点')
    expect(statusRow).toBeTruthy()
    const card1 = screen.getByTestId('mn-card1').textContent ?? ''
    expect(card1).toContain(NODES[0].name) // 名分同源
    expect(card1).toContain(NODES[0].sink)  // 下沉展示句同源（待复算）
  })
})
