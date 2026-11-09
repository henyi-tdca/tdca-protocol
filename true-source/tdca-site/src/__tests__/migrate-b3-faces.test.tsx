// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI206-MIGRATE-B3 批3 其余四面渲染自测
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-MIGRATE-B3-001 §四-1/5——
//   /channel 总入口（前置登记＋六步硬序＋子页入口）；
//   /contribute 三级台阶（三阶齐／机器人不代签口径／⛔ 承诺）；
//   /public-face 三栏照实；/private 三条铁句＋两域分工＋指路随轨 /channel/register
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'
import { ChannelPortalPage } from '@/pages/ChannelPortal'
import { ContributePage } from '@/pages/Contribute'
import { PublicFacePage } from '@/pages/PublicFace'
import { PrivateDomainPage } from '@/pages/PrivateDomain'
import { ROUTE_PATHS } from '@/pages/PagesIndex'

describe('MIGRATE-B3 路由注册：其余四面入册', () => {
  it('/channel、/contribute、/public-face、/private 入 ROUTE_PATHS', () => {
    for (const p of ['/channel', '/contribute', '/public-face', '/private']) {
      expect(ROUTE_PATHS).toContain(p)
    }
  })
})

describe('/channel 智能体通道总入口（批2 漏项补做）', () => {
  it('前置登记口径在（登记方为创建／幽灵态）', () => {
    render(<MemoryRouter><ChannelPortalPage /></MemoryRouter>)
    const pre = screen.getByTestId('channel-preregister').textContent ?? ''
    expect(pre).toContain('登记方为创建')
    expect(pre).toContain('幽灵态')
  })

  it('六步硬序六步齐（照在册条例第 19 条环节名）', () => {
    render(<MemoryRouter><ChannelPortalPage /></MemoryRouter>)
    const steps = ['①', '②', '③', '④', '⑤', '⑥'].map((n) => screen.getByTestId(`channel-step-${n}`).textContent ?? '')
    expect(steps[0]).toContain('加载 TDCA 协议')
    expect(steps[1]).toContain('持根节点执行令牌')
    expect(steps[2]).toContain('负空间审查')
    expect(steps[3]).toContain('沙盒验证')
    expect(steps[4]).toContain('正空间执行事务')
    expect(steps[5]).toContain('NCA 存证')
  })

  it('子页入口：自助登记随轨指 /channel/register（批2 并轨），五子通道面不动', () => {
    render(<MemoryRouter><ChannelPortalPage /></MemoryRouter>)
    const reg = screen.getByTestId('channel-entry-自助登记')
    expect(reg.getAttribute('href')).toBe('/channel/register')
    const my = screen.getByTestId('channel-entry-我的通道')
    expect(my.getAttribute('href')).toBe('/channel/my')
    // 五子通道面为既有路由（ChannelHome 批2 骨架），本页只指不建
    expect(screen.getByTestId('channel-entry-能力直达（旧路）').getAttribute('href')).toBe('/channel/agents')
    expect(screen.getByTestId('channel-entry-工具直达（旧路）').getAttribute('href')).toBe('/channel/tools')
  })
})

describe('/contribute 我要贡献 · 三级台阶', () => {
  it('三阶齐：viewer／贡献者／节点方', () => {
    render(<MemoryRouter><ContributePage /></MemoryRouter>)
    const tiers = screen.getAllByTestId('contribute-tier')
    expect(tiers).toHaveLength(3)
    expect(tiers[0].textContent).toContain('viewer')
    expect(tiers[1].textContent).toContain('贡献者')
    expect(tiers[2].textContent).toContain('节点方')
  })

  it('机器人不代签口径与「不承诺」句在；第三阶指路随轨 /channel/register', () => {
    render(<MemoryRouter><ContributePage /></MemoryRouter>)
    expect(screen.getByTestId('contribute-duty').textContent).toContain('机器人不代签、不代判')
    expect(screen.getByTestId('contribute-duty').textContent).toContain('不承诺')
    const roads = screen.getAllByTestId('contribute-road').map((e) => e.getAttribute('href'))
    expect(roads).toContain('/channel/register')
    expect(roads).toContain('/private')
    expect(roads).toContain('/ownership-registry')
  })
})

describe('/public-face 匿名可见面（三栏照实）', () => {
  it('可看／需登录／不开放三栏齐', () => {
    render(<MemoryRouter><PublicFacePage /></MemoryRouter>)
    expect(screen.getByTestId('public-face-table-public')).toBeTruthy()
    expect(screen.getByTestId('public-face-table-login')).toBeTruthy()
    expect(screen.getByTestId('public-face-table-closed')).toBeTruthy()
  })

  it('三栏行数照旧版清单（9／9／5）', () => {
    render(<MemoryRouter><PublicFacePage /></MemoryRouter>)
    expect(screen.getByTestId('public-face-table-public').querySelectorAll('tbody tr')).toHaveLength(9)
    expect(screen.getByTestId('public-face-table-login').querySelectorAll('tbody tr')).toHaveLength(9)
    expect(screen.getByTestId('public-face-table-closed').querySelectorAll('tbody tr')).toHaveLength(5)
  })
})

describe('/private 私域与边界 · 公域守门人', () => {
  it('三条铁句齐', () => {
    render(<MemoryRouter><PrivateDomainPage /></MemoryRouter>)
    const iron = screen.getByTestId('private-iron').textContent ?? ''
    expect(iron).toContain('获取方式 ≠ 已获授权')
    expect(iron).toContain('网站＝接口')
    expect(iron).toContain('私域内部可存在，对外协作必经公域')
  })

  it('两域分工＋两权闸门入口＋通道登记指路随轨 /channel/register', () => {
    render(<MemoryRouter><PrivateDomainPage /></MemoryRouter>)
    expect(screen.getByTestId('private-public').textContent).toContain('公域（站上管）')
    expect(screen.getByTestId('private-own').textContent).toContain('私域（节点所有者管）')
    expect(screen.getByTestId('private-road-ownership').getAttribute('href')).toBe('/ownership-registry')
    expect(screen.getByTestId('private-road-auth').getAttribute('href')).toBe('/authorization-registry')
    expect(screen.getByTestId('private-road-channel').getAttribute('href')).toBe('/channel/register')
  })
})
