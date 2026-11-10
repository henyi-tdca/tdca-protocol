// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 追平批B1（L1SI206-PARITY-B1）四面＋首页 Ω 验证
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-PARITY-FILL-001 §四验收——
//   ① 逐面可点（公开面）② 题名净名照旧版 ③ 索引三产物机算自洽
//   ④ /rules 五类分组·五态徽标·六步导航·折叠区·甲案注明（⛔ 标错态）
//   ⑤ /help 帮助族动态读＋联系块空栏为常态（⛔ 预置）；fail-closed 人话
//   ⑥ /negativespace 只讲原则与类别（⛔ 禁项词表）；三空间＋四机制＋红线注
//   ⑦ /academy/outline 原文照贴零改写；⑧ 首页 Ω 图形状与旧版一致（3 顶点 5 边）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { RulesMapPage } from '@/pages/rules/rules'
import { HelpPage } from '@/pages/HelpPage'
import { NegativeSpacePage } from '@/pages/NegativeSpacePage'
import { AcademyOutlinePage } from '@/pages/academy/AcademyOutlinePage'
import Home from '@/pages/Home'
import { PAGE_META, ROUTE_PATHS } from '@/pages/PagesIndex'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload }) as Response

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('追平批B1：/rules 制度地图（机读表唯一源）', () => {
  it('六步导航＋计数带＋五类分组渲染（56 件主表口径）', () => {
    render(<MemoryRouter><RulesMapPage /></MemoryRouter>)
    expect(screen.getByText('制度地图')).toBeTruthy()
    expect(screen.getByTestId('step-nav')).toBeTruthy()
    for (const s of ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']) {
      expect(screen.getByTestId('step-nav').textContent).toContain(s)
    }
    // S5/S6 待补标
    expect(screen.getByTestId('step-gap-S5')).toBeTruthy()
    expect(screen.getByTestId('step-gap-S6')).toBeTruthy()
    const band = screen.getByTestId('count-band').textContent ?? ''
    expect(band).toContain('主表 57 件') // 机读表实测主表 57 件（面表旧记 56，以表为准）
    // 五态计数俱全
    for (const st of ['生效', '指引性', '草案', '对外候选', '非制度件', '待辨']) {
      expect(band).toContain(st)
    }
    // 五类分组节
    for (const cls of ['基本制度', '条例', '规范与细则', '标准与流程', '模板与表单']) {
      expect(screen.getByTestId(`class-section-${cls}`)).toBeTruthy()
    }
  })

  it('行件五态徽标＋甲案必载注明＋历史草案折叠区', () => {
    render(<MemoryRouter><RulesMapPage /></MemoryRouter>)
    // 五态徽标渲染实例
    expect(screen.getAllByTestId('state-badge-生效').length).toBeGreaterThan(0)
    // 三族 9 件甲案注明（V1.0-FROZEN 且三族前缀）
    expect(screen.getAllByTestId('frozen-note').length).toBe(9)
    // 历史草案折叠区
    const archived = screen.getByTestId('rules-archived')
    expect(archived.textContent).toContain('历史草案')
  })

  it('点 S5 出待补横幅＋相邻件挂接（⛔ 以草案充数）', () => {
    render(<MemoryRouter><RulesMapPage /></MemoryRouter>)
    const s5btn = Array.from(screen.getByTestId('step-nav').querySelectorAll('button')).find((b) => b.textContent?.startsWith('S5')) as HTMLButtonElement
    fireEvent.click(s5btn)
    expect(screen.getByTestId('gap-banner').textContent).toContain('待补')
    expect(screen.getByTestId('gap-banner').textContent).toContain('⛔ 不以草案充数')
  })
})

describe('追平批B1：/help 帮助与联系（动态读＋空栏为常态）', () => {
  it('帮助族 404＝如实空栏（⛔ 不当作故障）', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 404, json: async () => ({}) }) as Response))
    render(<MemoryRouter><HelpPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByText('帮助族暂无入库文档（空栏为常态）。')).toBeTruthy())
    expect(screen.queryByTestId('help-fail-closed')).toBeNull()
    // 联系块如实空栏
    expect(screen.getByTestId('help-contact').textContent).toContain('官方联系渠道未入站')
  })

  it('帮助族在册：条目列出＋含「联系」者入联系块', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => okJson({
      family: 'help', count: 2,
      documents: [
        { family: 'help', slug: 'a', filename: '如何注册.md', version: 'V1', bytes: 1, sha256: 'x', sha256_16: 'y' },
        { family: 'help', slug: 'b', filename: '联系我们.md', version: 'V1', bytes: 1, sha256: 'x', sha256_16: 'y' },
      ],
    })))
    render(<MemoryRouter><HelpPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByText('如何注册')).toBeTruthy())
    expect(screen.getByTestId('help-contact').textContent).toContain('联系我们')
  })

  it('后端故障 fail-closed 人话兜底（⛔ 白屏）', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) }) as Response))
    render(<MemoryRouter><HelpPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('help-fail-closed')).toBeTruthy())
    expect(screen.getByTestId('help-fail-closed').textContent).toContain('[fail-closed] 帮助族暂不可用')
  })
})

describe('追平批B1：/negativespace 负空间（原则与类别，⛔ 禁项词表）', () => {
  it('三空间＋四机制＋红线注全在', () => {
    render(<MemoryRouter><NegativeSpacePage /></MemoryRouter>)
    expect(screen.getByTestId('negativespace-page')).toBeTruthy()
    for (const n of ['正空间', '负空间', '未裁决']) expect(screen.getByText(n)).toBeTruthy()
    for (const m of ['负空间函数语言（NSFL）', '负空间熔断', '拒绝清单', '公共负空间维护']) {
      expect(screen.getByText(m)).toBeTruthy()
    }
    const redline = screen.getByTestId('negativespace-redline').textContent ?? ''
    expect(redline).toContain('只讲原则与类别')
    expect(redline).toContain('不列、公开页面不转载')
    // 正文不含具体禁项词面（词表级红线由制度侧把守，本栏只到类别）
  })
})

describe('追平批B1：/academy/outline 教材目录（原文照贴）', () => {
  it('纲要渲染＋五卷口径＋返回链接', () => {
    render(<MemoryRouter><AcademyOutlinePage /></MemoryRouter>)
    expect(screen.getByTestId('biz-school-outline')).toBeTruthy()
    const doc = screen.getByTestId('biz-doc').textContent ?? ''
    expect(doc).toContain('TDCA 商学院教材')
    expect(doc).toContain('五卷')
    expect(doc).toContain('35') // 原文明载「五卷 ／ 35 章」（面表旧记「35 册」，以原字节为准）
    const back = screen.getByText('← 返回商学院').closest('a') as HTMLAnchorElement
    expect(back.getAttribute('href')).toBe('/academy')
  })
})

// jsdom 无 canvas：Ω 测试打桩 TopologyEngine（照旧例；page-home 用例走真实引擎不受影响）
vi.mock('@/lib/TopologyEngine', () => ({
  TopologyEngine: () => null,
  hashAgentId: (id: string) => 'hash-' + id,
}))

describe('追平批B1·10a：首页五元拓扑 Ω（AMEND-1 必办）', () => {
  it('Ω 图区在架：三顶点五边形状照旧版', () => {
    render(<MemoryRouter><Home /></MemoryRouter>)
    expect(screen.getByTestId('home-omega')).toBeTruthy()
    expect(screen.getByText('五元拓扑 Ω（H/M/L 顶点 ＋ 五关系边）')).toBeTruthy()
    // 现有五段不动：trinity/stages/join/machine 仍在
    for (const id of ['trinity', 'stages', 'join', 'machine']) {
      expect(document.getElementById(id)).toBeTruthy()
    }
  })
})

describe('追平批B1：站点地图入册（26→30）', () => {
  it('四面入册 ROUTE_PATHS（题名净名照旧版）', () => {
    expect(PAGE_META).toHaveLength(38) /* 追平批B4：+1（/verify） */ /* SMALL2-001：+2（/me/compile /me/privacy 入册） */
    const titles: Record<string, string> = {
      '/rules': '制度地图',
      '/help': '帮助与联系',
      '/negativespace': '负空间 · 什么不能做',
      '/academy/outline': '教材目录（纲要）',
    }
    for (const [path, title] of Object.entries(titles)) {
      expect(PAGE_META.find((m) => m.path === path)?.title).toBe(title)
      expect(ROUTE_PATHS).toContain(path)
    }
  })
})
