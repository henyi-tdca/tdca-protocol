// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI206-MIGRATE-B3 节点网络公域四块＋私域两卡自测
// 约束矩阵: NODE-NET-A-001 十条硬约束——真节点恰 1 个（⛔ 演示点）、零「实时」字样、九类接口齐、
//   未实现一律「建设中 · 未开放」唯文档/协议包分发可用、状态栏「数据截至 HH:MM」在、
//   私域七字段无真值如实「未设置／待复算」、卡底固定句原文、三处同源（唯一数据模块）
//   ＋ MIGRATE-B3-001 §四-3：私域卡未登录由接口 401/403 把守（前端隐藏 ⛔ 作据）
// 并轨注记: MIGRATE 批3 自旧树 __tests__/node-net-a.test.tsx 迁移适配——
//   ① 导入路径换新版（@/pages/NodeNet、MeNodeNet、@/lib/client）；
//   ② 路由注册断言换 ROUTE_PATHS（新树无 PAGE_COMPONENTS 注册表，组件直挂 App.tsx）；
//   ③ 私域卡两剧本：auth/me ok ⟹ 卡面全渲染；401 ⟹ 私域内容零渲染（新增，照批3 §四-3）；
//   ④ 公域四块断言一字未动。
// =============================================================================
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

// —— 门禁剧本：ok ⟹ 私域内容可见；401 ⟹ 私域内容零渲染（API 层把守） ——
let meScript: { ok: boolean } = { ok: true }
vi.mock('@/lib/client', () => ({
  api: {
    get: vi.fn(async (path: string) => {
      if (path.includes('/auth/me')) {
        return meScript.ok
          ? { ok: true, data: { username: 'founder' }, watermark: 'w', nature: 'real' }
          : { ok: false, reason: 'unauthorized', status: 401 }
      }
      return { ok: false, reason: 'http_error' }
    }),
    post: vi.fn(async () => ({ ok: false, reason: 'http_error' })),
  },
  loadDraft: () => null,
  saveDraft: () => undefined,
  clearDraft: () => undefined,
}))

import { MeNodeNetPage } from '@/pages/MeNodeNet'
import { NodeNetPage } from '@/pages/NodeNet'
import { NINE_APIS, NODES, NODE_REGULATION } from '@/pages/node-net-data'
import { ROUTE_PATHS } from '@/pages/PagesIndex'

describe('MIGRATE-B3 路由注册', () => {
  it('/me/node/net 与 /nodes 入 ROUTE_PATHS（新树 PAGE_META 在册）', () => {
    expect(ROUTE_PATHS).toContain('/me/node/net')
    expect(ROUTE_PATHS).toContain('/nodes')
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

describe('私域两卡：我的节点 / 条例与契约（门禁 ok 剧本）', () => {
  it('卡一七字段无真值如实标（未设置／待复算）＋卡底固定句', async () => {
    meScript = { ok: true }
    render(<MemoryRouter><MeNodeNetPage /></MemoryRouter>)
    const card1 = (await screen.findByTestId('mn-card1')).textContent ?? ''
    expect(card1).toContain('未设置')
    expect(card1).toContain('待复算')
    expect(card1).toContain('本节点为分层最低层场景；制度不减项、门槛不降低。')
  })

  it('卡二条例真值＋九类清单＋契约版本＋变更公告暂无', async () => {
    meScript = { ok: true }
    render(<MemoryRouter><MeNodeNetPage /></MemoryRouter>)
    const card2 = (await screen.findByTestId('mn-card2')).textContent ?? ''
    expect(card2).toContain('业务端节点接入与同构契约条例')
    expect(card2).toContain('已生效')
    expect(screen.getAllByTestId('mn-api-chip')).toHaveLength(9)
    expect(card2).toContain('变更公告')
    expect(card2).toContain('暂无')
  })

  it('下载两链指向 /docs/regulation 在册件名', async () => {
    meScript = { ok: true }
    render(<MemoryRouter><MeNodeNetPage /></MemoryRouter>)
    expect((await screen.findByTestId('mn-reg-human')).getAttribute('href')).toContain('/docs/regulation/')
    expect(screen.getByTestId('mn-reg-machine').getAttribute('href')).toContain('COMPILED')
  })
})

describe('私域两卡：门禁 401 剧本（批3 §四-3：API 层把守，前端隐藏 ⛔ 作据）', () => {
  it('未登录 ⟹ 人话提示在、私域卡内容零渲染', async () => {
    meScript = { ok: false }
    render(<MemoryRouter><MeNodeNetPage /></MemoryRouter>)
    expect(await screen.findByTestId('private-gate-denied')).toBeTruthy()
    expect(screen.queryByTestId('mn-card1')).toBeNull()
    expect(screen.queryByTestId('mn-card2')).toBeNull()
    // 页壳在（公开面可达），私域数据不露
    expect(screen.getByTestId('me-node-net-page')).toBeTruthy()
  })
})

describe('三处同源（硬约束八）', () => {
  it('私域卡与公域状态栏读同一数据模块', async () => {
    meScript = { ok: true }
    render(<MemoryRouter><><MeNodeNetPage /><NodeNetPage /></></MemoryRouter>)
    await screen.findByTestId('mn-card1')
    const statusRow = within(screen.getAllByTestId('nn-status-row')[0]).getByText('创世节点')
    expect(statusRow).toBeTruthy()
    const card1 = screen.getByTestId('mn-card1').textContent ?? ''
    expect(card1).toContain(NODES[0].name) // 名分同源
    expect(card1).toContain(NODES[0].sink)  // 下沉展示句同源（待复算）
  })
})
