// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI163-START-001 /start 新手指引自检
// 约束矩阵: 设计件 §五 A-1~A-10（计数程序统计，⛔ 目测）＋ §四 M-1~M-4 同批验收
//  验①哈希：?raw 源 sha256_16 == 在册值 DE72CA35429AF099（_START-MAP-20261021-V1·R1-001-A 实测刷新）
//  验②解析：steps 6／docs 56／terms 147；六步 5/24/17/26/2/3；五类 21/17/9/5/4；
//           五态 27/17/5/4/3；page_visible 54＋折叠 2（相遇 V0.9）；adjacent_steps 口径；
//           RTN 两义 T-029/T-034 并列在册
//  验③渲染：A-2 六步名逐字／A-3 步内件数（page_visible 在列 5/22/17/24/2/3，
//           徽数照 STEP 表 5/24/17/26/2/3，差值即折叠件并注明）／A-4 缺口两处同标／
//           A-5 相邻件文案与 adjacent_steps 一致／A-6 筛选叠加抽测 8 组（含两组空组合）／
//           A-7 术语检索 147 全集＋T-### 跳转链接／A-8 RTN 并列不合并／
//           A-9 数据源文案「_START-MAP 三表」／A-10+M-4 data=null 兜底不白屏
// =============================================================================
import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'
import { StartPageBody } from '@/pages/start/start'
import { parseStartMap } from '@/pages/start/parse'
import { RulesMapPage } from '@/pages/rules/rules'
import startMapYaml from '@/pages/start/start-map.yaml?raw'

/** WebCrypto 标准接口（零新依赖；与 node:crypto 同为 SHA-256） */
async function sha16(s: string) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s))
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase()
    .slice(0, 16)
}

const DATA = parseStartMap(startMapYaml)
const VISIBLE = DATA.docs.filter((d) => d.page_visible)

function renderStart() {
  return render(
    <MemoryRouter>
      <StartPageBody data={DATA} />
    </MemoryRouter>,
  )
}

/** 筛选叠加的独立期望值（与实现同口径重算：raw 态筛选＋显示态归一入关键词） */
function expectCatalog(
  cls: string | null,
  state: string | null,
  step: string | null,
  kw: string,
): number {
  const needle = kw.trim().toLowerCase()
  return DATA.docs
    .filter((d) => (cls ? d.class === cls : true))
    .filter((d) => (state ? d.state === state : true))
    .filter((d) => (step ? d.steps.includes(step) : true))
    .filter((d) => {
      if (needle === '') return true
      const hay = [...d.keys, d.state === '对外候选' ? '生效' : d.state, ...d.steps]
        .join('\n')
        .toLowerCase()
      return hay.includes(needle)
    }).length
}

function applyCatalog(
  cls: string | null,
  state: string | null,
  step: string | null,
  kw: string,
) {
  renderStart()
  if (cls) fireEvent.click(screen.getByTestId(`catalog-chip-class-${cls}`))
  if (state) fireEvent.click(screen.getByTestId(`catalog-chip-state-${state}`))
  if (step) fireEvent.click(screen.getByTestId(`catalog-chip-step-${step}`))
  if (kw !== '') fireEvent.change(screen.getByTestId('catalog-kw'), { target: { value: kw } })
  return screen.getByTestId('catalog')
}

describe('验①② 机读表哈希与解析（A-3 程序统计）', () => {
  it('?raw 源 sha256_16 == 在册值 0CE5C89A957B6B60', async () => {
    expect(await sha16(startMapYaml)).toBe('DE72CA35429AF099')
  })

  it('三表规模：steps 6／docs 56／terms 147／组 12', () => {
    expect(DATA.steps).toHaveLength(6)
    expect(DATA.docs).toHaveLength(56)
    expect(DATA.terms).toHaveLength(147)
    expect(new Set(DATA.terms.map((t) => t.group)).size).toBe(12)
  })

  it('六步计数 5/24/17/26/2/3（STEP 表 count 字段）＋缺口标记仅 S5/S6', () => {
    const want = { S1: 5, S2: 24, S3: 17, S4: 26, S5: 2, S6: 3 }
    for (const s of DATA.steps) {
      expect(s.count, s.key).toBe(want[s.key as keyof typeof want])
      expect(s.gap, s.key).toBe(s.key === 'S5' || s.key === 'S6')
    }
  })

  it('五类 21/17/9/5/4（全 56）；五态 27/17/5/4/3（全 56）；page_visible 54＋折叠 2（相遇 V0.9）', () => {
    for (const [cls, n] of Object.entries({ 条例: 21, 标准与流程: 17, 规范与细则: 9, 模板与表单: 5, 基本制度: 4 })) {
      expect(DATA.docs.filter((d) => d.class === cls), cls).toHaveLength(n)
    }
    for (const [st, n] of Object.entries({ 生效: 27, 指引性: 17, 草案: 5, 对外候选: 4, 非制度件: 3 })) {
      expect(DATA.docs.filter((d) => d.state === st), st).toHaveLength(n)
    }
    expect(VISIBLE).toHaveLength(54)
    const folded = DATA.docs.filter((d) => !d.page_visible)
    expect(folded).toHaveLength(2)
    for (const f of folded) expect(f.filename).toContain('V0.9-DRAFT')
  })

  it('相邻件口径＝本步前两步＋后一步（S1=[S2]／S5=[S3,S4,S6]／S6=[S4,S5]）', () => {
    const byKey = new Map(DATA.steps.map((s) => [s.key, s.adjacent_steps]))
    expect(byKey.get('S1')).toEqual(['S2'])
    expect(byKey.get('S5')).toEqual(['S3', 'S4', 'S6'])
    expect(byKey.get('S6')).toEqual(['S4', 'S5'])
  })

  it('RTN 两义在册：T-029（RTN）与 T-034（RTN（协议层轧差））并列不合并', () => {
    const rtn = DATA.terms.filter((t) => t.name === 'RTN' || t.name === 'RTN（协议层轧差）')
    expect(rtn.map((t) => t.id).sort()).toEqual(['T-029', 'T-034'])
  })
})

describe('验③ 渲染（A-2~A-5）', () => {
  it('A-2 六步卡片齐、名称与设计件 §一 逐字一致', () => {
    renderStart()
    const want = [
      ['S1', '了解 TDCA'],
      ['S2', '读懂基本制度'],
      ['S3', '看资产与授权'],
      ['S4', '参与协作'],
      ['S5', '结算与计税'],
      ['S6', '争议与退出'],
    ] as const
    for (const [k, label] of want) {
      const card = screen.getByTestId(`step-card-${k}`)
      expect(card.textContent).toContain(`${k} ${label}`)
    }
  })

  it('A-3 步内只列 page_visible：S2 在列 22（徽数 24，注明折叠 2）；S5/S6 在列 2/3', () => {
    renderStart()
    fireEvent.click(screen.getByTestId('step-card-S2'))
    const sec = screen.getByTestId('step-docs')
    const s2vis = VISIBLE.filter((d) => d.steps.includes('S2')).length
    expect(within(sec).getAllByTestId('start-doc-row')).toHaveLength(s2vis)
    expect(sec.textContent).toContain('本步在列 22 件')
    // 徽数照 STEP 表（24），差 2 即历史草案，页面注明
    expect(screen.getByTestId('step-card-S2').textContent).toContain('24 件')
    expect(sec.textContent).toContain('历史草案 2 件')
    // 缺口步：相邻件表与本步件同列于 step-docs 区内，须扣除相邻件再数
    const mainRowCount = () => {
      const total = within(screen.getByTestId('step-docs')).getAllByTestId('start-doc-row').length
      const adj = screen.queryByTestId('adjacent-docs')
      const adjN = adj ? within(adj).getAllByTestId('start-doc-row').length : 0
      return total - adjN
    }
    fireEvent.click(screen.getByTestId('step-card-S5'))
    expect(mainRowCount()).toBe(2)
    fireEvent.click(screen.getByTestId('step-card-S6'))
    expect(mainRowCount()).toBe(3)
  })

  it('A-4 缺口两处同标：S5 横幅＋按钮角标同时现「待补」；非缺口步无角标', () => {
    renderStart()
    expect(screen.queryByTestId('step-gap-S1')).toBeNull()
    fireEvent.click(screen.getByTestId('step-card-S5'))
    expect(screen.getByTestId('gap-banner').textContent).toContain('待补')
    expect(screen.getByTestId('step-gap-S5').textContent).toContain('待补')
    expect(screen.getByTestId('gap-banner').textContent).toContain('本步制度件尚在补足途中（⛔ 不以草案充数）')
  })

  it('A-5 相邻件文案与 adjacent_steps 计算一致（S5：前三步域 S3/S4/S6 的 page_visible 件数）', () => {
    renderStart()
    fireEvent.click(screen.getByTestId('step-card-S5'))
    const adj = new Set(DATA.steps.find((s) => s.key === 'S5')!.adjacent_steps)
    const n = VISIBLE.filter((d) => d.steps.some((s) => adj.has(s))).length
    expect(screen.getByTestId('gap-banner').textContent).toContain(`相邻件（本步前两步 ＋ 后一步）挂接 ${n} 件`)
    expect(within(screen.getByTestId('adjacent-docs')).getAllByTestId('start-doc-row')).toHaveLength(n)
  })
})

describe('A-6 目录筛选叠加（抽测 8 组，含两组空组合）', () => {
  const combos: [string | null, string | null, string | null, string][] = [
    [null, '生效', null, ''],
    ['条例', null, null, ''],
    [null, null, 'S2', ''],
    ['条例', '生效', null, ''],
    ['条例', '生效', 'S2', ''],
    [null, null, null, '相遇'],
    [null, '生效', 'S5', ''],
    ['模板与表单', '生效', 'S1', ''],
  ]
  for (const [cls, state, step, kw] of combos) {
    const label = `类=${cls ?? '∅'} 态=${state ?? '∅'} 步=${step ?? '∅'} 词=${kw || '∅'}`
    it(`组合 ${label} → ${expectCatalog(cls, state, step, kw)} 件`, () => {
      const catalog = applyCatalog(cls, state, step, kw)
      const want = expectCatalog(cls, state, step, kw)
      expect(within(catalog).queryAllByTestId('start-doc-row'), label).toHaveLength(want)
      expect(screen.getByTestId('catalog-count').textContent, label).toContain(`${want} 件`)
      if (want === 0) {
        expect(screen.getByTestId('catalog-empty').textContent).toContain('本组合无件，换个条件试试')
      }
    })
  }

  it('态芯片计数与 §2.1 一致（生效 27／指引性 17／草案 5／对外候选 4／非制度件 3）', () => {
    renderStart()
    const want = { 生效: 27, 指引性: 17, 草案: 5, 对外候选: 4, 非制度件: 3 } as const
    for (const [st, n] of Object.entries(want)) {
      expect(screen.getByTestId(`catalog-chip-state-${st}`).textContent).toContain(`${st} ${n}`)
    }
  })
})

describe('A-7/A-8 术语检索与跳转', () => {
  it('空检索命中 147 全集；按 id／name／short_def 匹配', () => {
    renderStart()
    expect(within(screen.getByTestId('terms')).getAllByTestId('term-card')).toHaveLength(147)
    fireEvent.change(screen.getByTestId('term-kw'), { target: { value: 'T-034' } })
    expect(within(screen.getByTestId('terms')).getAllByTestId('term-card')).toHaveLength(1)
    fireEvent.change(screen.getByTestId('term-kw'), { target: { value: '轧差' } })
    const cards = within(screen.getByTestId('terms')).getAllByTestId('term-card')
    expect(cards.length).toBeGreaterThan(0)
    expect(cards.some((c) => c.textContent!.includes('T-034'))).toBe(true)
  })

  it('A-8 RTN 两义并列不合并（T-029 与 T-034 同列）', () => {
    renderStart()
    fireEvent.change(screen.getByTestId('term-kw'), { target: { value: 'RTN' } })
    const cards = within(screen.getByTestId('terms')).getAllByTestId('term-card')
    const ids = cards.map((c) => within(c).getByTestId('term-id').textContent)
    expect(ids).toContain('T-029')
    expect(ids).toContain('T-034')
  })

  it('A-7 正文 T-### 生成跳转锚链（short_def 含 T 号者，可引用他词）', () => {
    renderStart()
    const withRef = DATA.terms.find((t) => /T-\d{3}/.test(t.short_def))!
    expect(withRef).toBeTruthy()
    const refId = withRef.short_def.match(/T-\d{3}/)![0]
    const card = within(screen.getByTestId('terms'))
      .getAllByTestId('term-card')
      .find((c) => within(c).getByTestId('term-id').textContent === withRef.id)!
    const link = card.querySelector('a[href^="#term-"]')
    expect(link).not.toBeNull()
    expect(link!.getAttribute('href')).toBe(`#term-${refId}`)
    expect(card.id).toBe(`term-${withRef.id}`)
  })

  it('术语卡反向查为接口位（本批未接通）', () => {
    renderStart()
    const first = within(screen.getByTestId('terms')).getAllByTestId('term-card')[0]
    expect(first.textContent).toContain('反向查接口位')
  })
})

describe('A-9 数据源文案（M-3）', () => {
  it('/start 显示「_START-MAP 三表（单一事实源）」；页尾数据源句在位', () => {
    renderStart()
    expect(screen.getByTestId('page-shell').textContent).toContain('_START-MAP 三表（单一事实源·仓内单源 ?raw 进包）')
    expect(screen.getByTestId('source-note').textContent).toBe(
      '本页数据源：_START-MAP 三表（单一事实源）· 制度件以 /rules 为准 · 术语以术语登记表为准',
    )
  })

  it('/rules 数据源改为仓内单源口径（M-3），不再称 GET 族面', () => {
    render(
      <MemoryRouter>
        <RulesMapPage />
      </MemoryRouter>,
    )
    const shell = screen.getByTestId('page-shell')
    expect(shell.textContent).toContain('机读表 _DOC-MAP-RULES-20261021-V6.1-FINAL（页面与检索同一源·仓内单源 ?raw 进包）')
    expect(shell.textContent).not.toContain('GET /api/site/docs 族面')
  })
})

describe('A-10 / M-1 / M-2 / M-4 兜底与 MINOR', () => {
  it('M-4：data=null 不白屏——提示＋六步骨架', () => {
    render(
      <MemoryRouter>
        <StartPageBody data={null} />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('load-error').textContent).toContain('本次数据加载失败，请稍后重试')
    const grid = screen.getByTestId('step-cards')
    expect(within(grid).getByTestId('step-card-S1').textContent).toContain('了解 TDCA')
    expect(within(grid).getByTestId('step-card-S6').textContent).toContain('争议与退出')
  })

  it('M-4：parseStartMap 对损坏输入抛错（组件侧 try/catch 接住）', () => {
    expect(() => parseStartMap('garbage: no sections here')).toThrow()
  })

  it('M-1：/rules 相邻件文案与算法同口径（S4／S6 字样已去）', () => {
    render(
      <MemoryRouter>
        <RulesMapPage />
      </MemoryRouter>,
    )
    fireEvent.click(within(screen.getByTestId('step-nav')).getByRole('button', { name: /S5 结算与计税/ }))
    expect(screen.getByTestId('gap-banner').textContent).toContain('相邻件（本步前两步 ＋ 后一步）挂接')
    expect(screen.getByTestId('gap-banner').textContent).not.toContain('S4／S6 侧')
  })

  it('M-2：/rules 缺口步按钮带「待补」角标；非缺口步无', () => {
    render(
      <MemoryRouter>
        <RulesMapPage />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('step-gap-S5').textContent).toContain('待补')
    expect(screen.getByTestId('step-gap-S6').textContent).toContain('待补')
    expect(screen.queryByTestId('step-gap-S1')).toBeNull()
    expect(screen.queryByTestId('step-gap-S3')).toBeNull()
  })
})
