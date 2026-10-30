// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B2 前三包测试（S2-3／S2-5／S2-6）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B2-001 §五验收六条——
//   三页 200 内容真（路由注册齐）；三问无判定结论＋真实性由本人负责；
//   三台阶各含要什么件／走哪条路＋不代签不代判；两域两权三铁句齐；
//   页面零内部编号零价格
// =============================================================================
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ThreeQuestionsPage } from '@/pages/three-questions'
import { ContributePage } from '@/pages/contribute'
import { PrivateDomainPage } from '@/pages/private-domain'
import { HelpPage } from '@/pages/help'
import { AboutPage } from '@/pages/about'
import { StartPageBody } from '@/pages/start/start'
import { parseStartMap } from '@/pages/start/parse'
import startMapYaml from '@/pages/start/start-map.yaml?raw'
import { PAGE_COMPONENTS, ROUTE_PATHS } from '@/pages/pages'

const startData = parseStartMap(startMapYaml)

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 404, json: async () => ({ detail: 'nf' }) }) as Response))
})
afterEach(() => { vi.unstubAllGlobals() })

describe('L1SI175-B2 前三包：路由注册', () => {
  it('三路径入 ROUTE_PATHS 且组件映射齐', () => {
    for (const p of ['/start/three-questions', '/contribute', '/private']) {
      expect(ROUTE_PATHS).toContain(p)
      expect(PAGE_COMPONENTS[p]).toBeTruthy()
    }
  })
})

describe('S2-3 三问向导（⛔ 代判·只汇总）', () => {
  it('三问齐＋必写句＋无判定结论', () => {
    render(<MemoryRouter><ThreeQuestionsPage /></MemoryRouter>)
    const text = document.body.textContent ?? ''
    expect(text).toContain('这是你自己原创的吗？')
    expect(text).toContain('是否用过 AI 工具？')
    expect(text).toContain('用在什么场景？')
    expect(text).toContain('你的回答会作为登记自述，真实性由你本人负责')
    expect(text).toContain('只汇总')
    // ⛔ 代判：不出现判定结论话术
    expect(text).not.toContain('判定结果')
    expect(text).not.toContain('恭喜')
  })

  it('逐问作答＋回退改＋汇出自述可复制', () => {
    render(<MemoryRouter><ThreeQuestionsPage /></MemoryRouter>)
    // 第一问：先选「完全原创」，前进
    fireEvent.click(screen.getAllByTestId('threeq-choice-0')[0])
    fireEvent.click(screen.getByTestId('threeq-next'))
    // 第二问：选「没用过」
    fireEvent.click(screen.getAllByTestId('threeq-choice-1')[0])
    // 回退修改第一问
    fireEvent.click(screen.getByTestId('threeq-back'))
    fireEvent.click(screen.getAllByTestId('threeq-choice-0')[1])
    fireEvent.click(screen.getByTestId('threeq-next'))
    // 第二问答案保留，前进到第三问
    fireEvent.click(screen.getByTestId('threeq-next'))
    // 第三问：作答＋补充
    fireEvent.click(screen.getAllByTestId('threeq-choice-2')[0])
    fireEvent.change(screen.getByTestId('threeq-note'), { target: { value: '用于课堂教学演示' } })
    const st = screen.getByTestId('threeq-statement')
    expect(st.textContent).toContain('登记自述')
    expect(st.textContent).toContain('部分借助了现成素材（补充里注明来源）')
    expect(st.textContent).toContain('没用过')
    expect(st.textContent).toContain('个人学习或研究')
    expect(st.textContent).toContain('用于课堂教学演示')
    expect(screen.getByTestId('threeq-copy')).toBeTruthy()
  })

  it('不出提交按钮：暂存本页＋真因（上传与登记提交接口待建）', () => {
    render(<MemoryRouter><ThreeQuestionsPage /></MemoryRouter>)
    const text = document.body.textContent ?? ''
    expect(text).toContain('暂存本页，提交功能在建')
    expect(text).toContain('上传与登记提交接口待建')
    // ⛔ 假提交：全文无「提交」按钮（说明文字里的「提交功能在建」不是按钮）
    const buttons = [...document.querySelectorAll('button')].map((b) => b.textContent)
    expect(buttons.every((b) => !b?.includes('提交'))).toBe(true)
  })
})

describe('S2-5 我要贡献（三台阶·只指路）', () => {
  it('三台阶齐＋每阶三要素＋不代签不代判＋不承诺', () => {
    render(<MemoryRouter><ContributePage /></MemoryRouter>)
    const text = document.body.textContent ?? ''
    expect(text).toContain('viewer（注册即有）')
    expect(text).toContain('贡献者（交素材，得登记号）')
    expect(text).toContain('节点方（起你的私域节点）')
    const tiers = screen.getAllByTestId('contribute-tier')
    expect(tiers.length).toBe(3)
    for (const t of tiers) {
      expect(t.textContent).toContain('要什么件')
      expect(t.textContent).toContain('走哪条路')
      expect(t.textContent).toContain('什么算成')
    }
    expect(text).toContain('机器人不代签、不代判')
    expect(text).toContain('不承诺任何时限，也不承诺必过')
  })

  it('指路指向既有登记面＋未通处建设中带真因', () => {
    render(<MemoryRouter><ContributePage /></MemoryRouter>)
    const roads = screen.getAllByTestId('contribute-road').map((a) => a.getAttribute('href'))
    for (const p of ['/ownership-registry', '/authorization-registry', '/channel/registry', '/start/three-questions', '/register', '/private']) {
      expect(roads).toContain(p)
    }
    const pendings = screen.getAllByTestId('contribute-pending').map((p) => p.textContent ?? '')
    expect(pendings.some((p) => p.includes('建设中') && p.includes('上传接口待建'))).toBe(true)
    expect(pendings.some((p) => p.includes('建设中') && p.includes('待后端就绪'))).toBe(true)
  })
})

describe('S2-6 私域与边界（两域两权三铁句）', () => {
  it('两域分工＋两权闸门＋入口指引', () => {
    render(<MemoryRouter><PrivateDomainPage /></MemoryRouter>)
    const text = document.body.textContent ?? ''
    expect(text).toContain('公域（站上管）')
    expect(text).toContain('私域（节点所有者管）')
    expect(text).toContain('权属登记（这是谁的）')
    expect(text).toContain('合约备案（允许谁用、什么条件）')
    expect(screen.getByTestId('private-road-ownership').getAttribute('href')).toBe('/ownership-registry')
    expect(screen.getByTestId('private-road-auth').getAttribute('href')).toBe('/authorization-registry')
    expect(screen.getByTestId('private-road-channel').getAttribute('href')).toBe('/channel/registry')
  })

  it('三条铁句逐字在＋本地部署包建设中带真因', () => {
    render(<MemoryRouter><PrivateDomainPage /></MemoryRouter>)
    const text = document.body.textContent ?? ''
    expect(text).toContain('获取方式 ≠ 已获授权')
    expect(text).toContain('网站＝接口')
    expect(text).toContain('私域仓库')
    expect(text).toContain('对外协作必经公域')
    const pkg = screen.getByTestId('private-pkg-pending').textContent ?? ''
    expect(pkg).toContain('建设中')
    expect(pkg).toContain('待后端就绪')
    expect(text).toContain('口径与站内体系结构说明一致')
  })
})

describe('B2-002 三处入口引链（6186 放行令：只加一句一链）', () => {
  it('/start 两处：三问向导＋我要贡献', () => {
    render(<MemoryRouter initialEntries={['/start']}><StartPageBody data={startData} /></MemoryRouter>)
    const block = screen.getByTestId('start-b2-links')
    expect(block.textContent).toContain('动手前先自问三件事：是不是你原创、用没用 AI、用在什么场景')
    expect(screen.getByTestId('start-link-threeq')).toHaveAttribute('href', '/start/three-questions')
    expect(block.textContent).toContain('想知道自己能到哪一阶、每阶要什么件')
    expect(screen.getByTestId('start-link-contribute')).toHaveAttribute('href', '/contribute')
  })

  it('/help 一处：我要贡献（三条路既有文字未动）', () => {
    render(<MemoryRouter><HelpPage /></MemoryRouter>)
    const p = screen.getByTestId('help-b2-contribute')
    expect(p.textContent).toContain('想知道自己能到哪一阶、每阶要什么件')
    expect(p.querySelector('a[href="/contribute"]')).not.toBeNull()
    // 既有三条路文字原样
    expect(screen.getByTestId('help-path-contribute').textContent).toContain('智能体自助登记入口')
  })

  it('/about 一处：私域与边界', () => {
    render(<MemoryRouter><AboutPage /></MemoryRouter>)
    const p = screen.getByTestId('about-b2-private')
    expect(p.textContent).toContain('公域与私域怎么分、什么必须走公域')
    expect(p.querySelector('a[href="/private"]')).not.toBeNull()
  })
})

describe('B2 前三包：零内部编号零价格（DOM 级）', () => {
  it('三页渲染文本禁样全零（¥/￥/元/价格/档位/付费/EIOS-/EVT-/族编号）', () => {
    for (const [name, Page] of [
      ['threeq', ThreeQuestionsPage],
      ['contribute', ContributePage],
      ['private', PrivateDomainPage],
    ] as const) {
      const { container, unmount } = render(<MemoryRouter><Page /></MemoryRouter>)
      const text = container.textContent ?? ''
      for (const bad of ['¥', '￥', '元', '价格', '档位', '付费', 'EIOS-', 'EVT-']) {
        expect(text.includes(bad)).toBe(false)
      }
      expect(text.match(/(^|[^A-Za-z])([PAMS]-?\d)/g) ?? []).toEqual([])
      unmount()
    }
  })

  it('引链三处块文本零编号零价格（既有页全文不在本批范围）', () => {
    const s = render(<MemoryRouter initialEntries={['/start']}><StartPageBody data={startData} /></MemoryRouter>)
    const startText = s.container.querySelector('[data-testid="start-b2-links"]')?.textContent ?? ''
    s.unmount()
    const h = render(<MemoryRouter><HelpPage /></MemoryRouter>)
    const helpText = h.container.querySelector('[data-testid="help-b2-contribute"]')?.textContent ?? ''
    h.unmount()
    const a = render(<MemoryRouter><AboutPage /></MemoryRouter>)
    const aboutText = a.container.querySelector('[data-testid="about-b2-private"]')?.textContent ?? ''
    a.unmount()
    for (const text of [startText, helpText, aboutText]) {
      expect(text.length).toBeGreaterThan(0)
      for (const bad of ['¥', '￥', '价格', '档位', '付费', 'EIOS-', 'EVT-']) {
        expect(text.includes(bad)).toBe(false)
      }
    }
  })
})
