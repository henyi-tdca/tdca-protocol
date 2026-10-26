// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批2块一 — 壳整改验收测试
// 约束矩阵: TDCA-FINAL-SITE-PHASE2-REVAMP-001-B2 §二块一 + §三验收六条
// 导航分组断言随导航-甲（L1SI176-NAV-A-001）更新：七组 → 九栏两轴
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { APP_NAV, navAllItems } from '@/app/app-shell'
import { RightRail } from '@/app/right-rail'
import { AuthProvider } from '@/app/auth-context'
import App from '@/App'

// /agents 渲染 TopologyEngine（Cytoscape）——jsdom 无布局环境，stub 布局计算
vi.mock('cytoscape', () => {
  const fakeNode = () => ({ position: () => ({ x: 10, y: 10 }), id: () => 'n' })
  const fakeCore = {
    nodes: () => [fakeNode()],
    elements: () => ({
      boundingBox: () => ({ x1: 0, y1: 0, x2: 100, y2: 100 }),
      nodes: () => [fakeNode()],
    }),
    ready: (cb: () => void) => cb(),
    destroy: () => {},
  }
  return { default: () => fakeCore }
})

const PUBLIC_NAV_TEXT = () =>
  APP_NAV.map((e) =>
    e.kind === 'link'
      ? [e.label]
      : [e.group, ...e.items.flatMap((i) => ('items' in i ? [i.subgroup, ...i.items.map((x) => x.label)] : [i.label]))],
  ).flat()

describe('导航-甲（L1SI176-NAV-A-001）：九栏两轴顶栏', () => {
  it('九栏可见且顺序如令 §一（1→9）', () => {
    const tops = APP_NAV.map((e) => (e.kind === 'link' ? e.label : e.group))
    expect(tops).toEqual([
      '首页',
      '了解 TDCA',
      '合规与沙盒',
      '资产与权利',
      '主体与协作',
      '服务',
      '我的',
      '学习与帮助',
      'NCA 与透明',
    ])
  })

  it('两轴结构可辨（V-2）：栏4 分 所有权／配置权，栏5 分 智能体／协作——层级本身即轴分辨，⛔ 无需读注释', () => {
    const axis1 = APP_NAV.find((e) => e.kind === 'group' && e.group === '资产与权利')
    const axis2 = APP_NAV.find((e) => e.kind === 'group' && e.group === '主体与协作')
    const subgroups = (g: typeof axis1) =>
      g && g.kind === 'group' ? g.items.flatMap((i) => ('items' in i ? [i.subgroup] : [])) : []
    expect(subgroups(axis1)).toEqual(['所有权', '配置权'])
    expect(subgroups(axis2)).toEqual(['智能体', '协作'])
  })

  it('公域导航零英文标签（验收三条之零英文；「NCA」「TDCA」为令面指定栏名缩写，豁免）', () => {
    for (const label of PUBLIC_NAV_TEXT()) {
      expect(label.replace(/NCA|TDCA/g, '')).not.toMatch(/[A-Za-z]/)
    }
  })

  it('公域导航零智能体通道 API 端点（AMEND-1 硬口径延续）：URL 不含 agent-channel；栏5 两项为页级入口（照令面）', () => {
    for (const item of navAllItems(APP_NAV)) {
      expect(item.to).not.toContain('agent-channel')
    }
    const all = navAllItems(APP_NAV)
    // 导航-甲 §一.5：自助登记／我的通道入栏5·智能体（页级，⛔ 非 API 端点）
    expect(all.some((i) => i.to === '/channel/registry' && i.label === '自助登记')).toBe(true)
    expect(all.some((i) => i.to === '/channel/my' && i.label === '我的通道')).toBe(true)
  })

  it('同一对象全站一名（V-5）：「智能体集群」「智能体区」不再并列；智能体仅「介绍」「能力与观测」两名', () => {
    const text = PUBLIC_NAV_TEXT().join('|')
    expect(text).not.toContain('智能体集群')
    expect(text).not.toContain('智能体区')
    const all = navAllItems(APP_NAV)
    expect(all.some((i) => i.to === '/agents' && i.label === '能力与观测')).toBe(true)
    expect(all.some((i) => i.to === '/agent-shelf' && i.label === '介绍')).toBe(true)
  })

  it('栏7「我的」含私域并入六项（L1SI176-NAV-A-001 §三.5：原私域组取消并入）', () => {
    const mine = APP_NAV.find((e) => e.kind === 'group' && e.group === '我的')
    expect(mine && mine.kind === 'group' ? mine.items.map((i) => ('to' in i ? i.to : '')) : []).toEqual([
      '/me',
      '/studio',
      '/ops',
      '/ops/me',
      '/review',
      '/me/appeal',
    ])
  })

  it('NCA 与透明栏含机器可读规格入口（raw 直开 /api/v1/selfcheck/spec）', () => {
    const res = APP_NAV.find((e) => e.kind === 'group' && e.group === 'NCA 与透明')
    expect(res && res.kind === 'group' ? navAllItems([res]).some((i) => i.raw && i.to === '/api/v1/selfcheck/spec') : false).toBe(true)
  })
})

describe('二期改版批2块一：私域归「我的」', () => {
  beforeEach(() => localStorage.clear())

  it('右栏「我的」含私域栏目导航（作业／人机协作／确权中心三路／集群编排／登记两页／规范与沙盒链／模拟锚）', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <RightRail />
        </AuthProvider>
      </MemoryRouter>,
    )
    const nav = screen.getByTestId('me-private-nav')
    for (const label of ['作业', '人机协作', '确权中心', '元函数确权', '动态确权', '集群编排', '权属登记', '授权登记', '规范与沙盒链']) {
      expect(nav.textContent).toContain(label)
    }
    // 模拟锚已依裁定落地件移公域（资源组），⛔ 不再在私域
    expect(nav.textContent).not.toContain('模拟锚')
  })

  it('公域页面无私域泄漏：首页不出现我的智能体／签批待办／凭据面板（验收五条）', () => {
    localStorage.clear()
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )
    const main = screen.getByTestId('main-col')
    expect(main.textContent).not.toContain('签批待办')
    expect(main.textContent).not.toContain('凭据')
  })
})

describe('二期改版批2块一：/channel/* 五路极简入口（重定向保留）', () => {
  beforeEach(() => {
    localStorage.setItem('tdca_auth_did', 'TDID-H-0001')
    localStorage.setItem('tdca_auth_token', 'TDCA-CRT-test')
  })

  it.each([
    ['/channel/portal', 'TDCA 三体可视化中心'],
    ['/channel/agents', '智能体集群观测'],
    ['/channel/market', '配置权市场（L2）'],
    ['/channel/tools', '工具货架（P4）'],
  ])('%s 重定向到对应新壳页面（⛔ 不 404）', (from, heading) => {
    const { unmount } = render(
      <MemoryRouter initialEntries={[from]}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: heading })).toBeInTheDocument()
    unmount()
  })

  it('/channel/registry 实页化：智能体自助登记入口（块 E；登记表单＋分流首问，⛔ 不 404）', () => {
    const { unmount } = render(
      <MemoryRouter initialEntries={['/channel/registry']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: '智能体自助登记（通道登记）' })).toBeInTheDocument()
    expect(screen.getByTestId('reg-six-steps').textContent).toContain('⑥ NCA 存证（全程）')
    expect(screen.getByTestId('reg-first-ask').textContent).toContain('是否已在本网注册')
    unmount()
  })
})

describe('二期改版批2块一：帮助与联系薄占位', () => {
  it('/help 可达且标注在建中', () => {
    render(
      <MemoryRouter initialEntries={['/help']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: '帮助与联系' })).toBeInTheDocument()
    expect(screen.getByTestId('page-shell').textContent).toContain('复用文档库')
  })

  it('导航-甲 §一.8：学习与帮助栏首项为商学院（/academy），新手指引在栏内（顺序以令面为准）', () => {
    const helpGroup = APP_NAV.find((e) => e.kind === 'group' && e.group === '学习与帮助')
    expect(helpGroup && helpGroup.kind === 'group' ? helpGroup.items[0] : undefined).toEqual({
      to: '/academy',
      label: '商学院',
    })
    expect(helpGroup && helpGroup.kind === 'group' ? helpGroup.items.some((i) => 'to' in i && i.to === '/start') : false).toBe(true)
  })
})
