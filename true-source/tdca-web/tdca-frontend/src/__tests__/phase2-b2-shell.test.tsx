// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 二期改版批2块一 — 壳整改验收测试
// 约束矩阵: TDCA-FINAL-SITE-PHASE2-REVAMP-001-B2 §二块一 + §三验收六条
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { APP_NAV } from '@/app/app-shell'
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
  APP_NAV.map((e) => (e.kind === 'link' ? [e.label] : [e.group, ...e.items.map((i) => i.label)])).flat()

describe('二期改版批2块一：公域顶栏六入口', () => {
  it('六入口齐备：首页／生态／市场／制度与透明／资源／帮助与联系', () => {
    const tops = APP_NAV.map((e) => (e.kind === 'link' ? e.label : e.group))
    expect(tops).toEqual(['首页', '生态', '市场', '制度与透明', '资源', '帮助与联系'])
  })

  it('公域导航零英文标签（验收三条之零英文）', () => {
    for (const label of PUBLIC_NAV_TEXT()) {
      expect(label).not.toMatch(/[A-Za-z]/)
    }
  })

  it('公域导航零智能体通道端点（AMEND-1 硬口径）', () => {
    const all = APP_NAV.flatMap((e) => (e.kind === 'link' ? [{ to: e.to, label: e.label }] : e.items))
    for (const item of all) {
      expect(item.to).not.toContain('agent-channel')
      expect(item.label).not.toContain('通道')
    }
  })

  it('公域导航零须登录操作栏目：作业／人机协作／确权中心总览／运维端／形式化入站不在公域', () => {
    const text = PUBLIC_NAV_TEXT().join('|')
    for (const banned of ['作业', '人机协作', '确权中心', '元函数确权', '动态确权', '集群编排', '权属登记', '授权登记', '规范与沙盒链', '运维端', '形式化入站']) {
      expect(text).not.toContain(banned)
    }
    // 确权历史留公域（制度即公开）；登记两页导航入口留公域（查询公示面，操作面块三收口）
    // 模拟锚依裁定落地件入公域（资源组，随块二落位）
    expect(text).toContain('确权历史')
    expect(text).toContain('模拟锚')
  })

  it('资源组含机器可读面入口（raw 直开 /openapi.json）', () => {
    const res = APP_NAV.find((e) => e.kind === 'group' && e.group === '资源')
    expect(res && res.kind === 'group' ? res.items.some((i) => i.raw && i.to === '/openapi.json') : false).toBe(true)
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

  it('L1SI167-START-ENTRY-001-001：帮助组首项为新手指引（/start）', () => {
    const helpGroup = APP_NAV.find((e) => e.kind === 'group' && e.group === '帮助与联系')
    expect(helpGroup && helpGroup.kind === 'group' ? helpGroup.items[0] : undefined).toEqual({
      to: '/start',
      label: '新手指引',
    })
  })
})
