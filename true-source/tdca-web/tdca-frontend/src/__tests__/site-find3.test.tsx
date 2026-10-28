// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI177 批3（SITE-FIND-CODE-001）三件自检
// 约束矩阵: 批3动码施工令 §三（九条自检之：编号形态零命中／索引⊆白名单／每条带数据性质／
//          两态／三卡三态五项／撤回灰态／首页条一行高／搜索框一行不霸屏）
// SPDX-License-Identifier: TDCA-Internal
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, act } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router'
import indexJson from '../../public/search-index.json'
import whitelistPy from '../../../gateway/public_docs_ops.py?raw'
import pagesSrc from '../pages/pages.tsx?raw'
import { SearchPage } from '@/pages/search'
import {
  __resetSearchIndexCacheForTest,
  searchEntries,
  splitForHighlight,
  type SearchIndexDoc,
} from '@/shared/search-index'
import { ToolshelfPage } from '@/pages/toolshelf'
import { AnnouncementsPage } from '@/pages/announcements'
import { HomeNoticeBar } from '@/app/notice-bar'
import { SearchBox } from '@/app/search-box'

// ------------------------------------------------------------ 测试用迷你索引
const MINI_INDEX: SearchIndexDoc = {
  spec: 'TDCA-SEARCH-INDEX-V1',
  generated_at: '2026-10-28T00:00:00Z',
  generated_by: 'site-find3.test',
  sources: {},
  counts: { 制度: 1, 白皮书: 1, 论文: 1, 素材: 1, 术语: 1, 栏目: 1 },
  total: 6,
  entries: [
    { title: '确权结算与配置权市场规范', family: '制度', summary: '配置权市场的准入与结算。', keywords: ['market'], url: '/docs/regulation/a.md', version: 'V1.0-FROZEN', nature: 'real', body: '正文谈确权底座机制' },
    { title: '制度哲学（中文版）', family: '论文', summary: '述及确权与结算闭环的方法论根。', keywords: [], url: '/docs/papers/b.md', version: 'V1.0', nature: 'real', body: '' },
    { title: '囚徒困境 · 思维协议', family: '素材', summary: '个体理性与集体非理性的博弈推理范式。', keywords: [], url: '/docs/cop-library/c.yaml', version: '', nature: 'synthetic', body: '正文述及确权底座机制，展开论述' },
    { title: '唯物主义白皮书', family: '白皮书', summary: '世界观与方法论双层奠基。', keywords: [], url: '/docs/whitepapers/d.md', version: 'V1.0', nature: 'real', body: '' },
    { title: '生态准入基协议（术语）', family: '术语', summary: '素材库件的可信底座机制名。', keywords: ['nca'], url: '/terms', version: '', nature: 'real', body: 'NCA 存证与准入门' },
    { title: '关于 · 一页看懂 TDCA', family: '栏目', summary: '面向普通读者的一页通俗说明。', keywords: [], url: '/about', version: '', nature: 'real', body: '' },
  ],
}

function envelope(payload: unknown, nature = 'real') {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-10-28T00:00:00Z', data_nature: nature }
}

/** 只答索引，其余 404（fail-closed 常态） */
function mockIndexFetch() {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (String(url).includes('search-index.json')) {
      return { ok: true, status: 200, json: async () => MINI_INDEX } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
  }))
}

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  __resetSearchIndexCacheForTest()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

// ------------------------------------------------------------ A 块：排序与高亮
describe('批3 A块 · 本地检索排序与高亮', () => {
  it('档位：标题＞摘要＞正文；同权重制度族优先', () => {
    const r = searchEntries(MINI_INDEX.entries, '确权')
    const titles = r.map((x) => x.entry.title)
    // 标题档（制度）最前
    expect(titles[0]).toBe('确权结算与配置权市场规范')
    // 摘要档（论文）先于正文档（素材）
    expect(titles.indexOf('制度哲学（中文版）')).toBeGreaterThan(0)
    expect(titles.indexOf('制度哲学（中文版）')).toBeLessThan(titles.indexOf('囚徒困境 · 思维协议'))
  })

  it('多术语 AND 语义：各术语均需命中', () => {
    const r = searchEntries(MINI_INDEX.entries, '确权 底座')
    expect(r.length).toBe(2)
    const both = searchEntries(MINI_INDEX.entries, '确权 不存在的词xyz')
    expect(both.length).toBe(0)
  })

  it('splitForHighlight：命中段标记正确（含大小写不敏感）', () => {
    const parts = splitForHighlight('NCA 确权与 nca 存证', 'nca')
    const hits = parts.filter((p) => p.hit).map((p) => p.text)
    expect(hits).toEqual(['NCA', 'nca'])
  })
})

// ------------------------------------------------------------ A 块：检索页两态
describe('批3 A块 · /search 两态', () => {
  it('态A 有结果：五条信息齐（标题／族／版本／性质／摘要），命中词 <mark> 高亮', async () => {
    mockIndexFetch()
    const { container } = render(
      <MemoryRouter initialEntries={['/search?q=确权']}>
        <SearchPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('search-results')).toBeTruthy())
    const results = screen.getAllByTestId('search-result')
    expect(results.length).toBe(3)
    expect(results[0].textContent).toContain('确权结算与配置权市场规范')
    expect(results[0].textContent).toContain('制度')
    expect(results[0].textContent).toContain('V1.0-FROZEN')
    expect(results[0].textContent).toContain('真实')
    expect(results[0].textContent).toContain('摘要')
    expect(container.querySelectorAll('mark').length).toBeGreaterThan(0)
  })

  it('态B 空结果：一句人话＋三族入口按钮', async () => {
    mockIndexFetch()
    render(
      <MemoryRouter initialEntries={['/search?q=量子引力']}>
        <SearchPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('search-empty')).toBeTruthy())
    expect(screen.getByTestId('search-empty').textContent).toContain('没找到「量子引力」相关结果')
    const links = screen.getAllByRole('link', { name: /^(制度|论文|素材)$/ })
    expect(links.map((l) => l.getAttribute('href'))).toEqual([
      '/docs/regulation',
      '/docs/papers',
      '/docs/cop-library',
    ])
  })

  it('索引不可用 → fail-closed 明示，不臆造结果', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 404, json: async () => ({ detail: 'not found' }) }) as Response))
    render(
      <MemoryRouter initialEntries={['/search?q=确权']}>
        <SearchPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('search-fail-closed')).toBeTruthy())
    expect(screen.queryByTestId('search-result')).toBeNull()
  })
})

// ------------------------------------------------------------ A 块：页头搜索框
describe('批3 A块 · 页头工具条层搜索入口', () => {
  it('一行 flex-nowrap 表单；提交跳 /search?q=', () => {
    function Probe() {
      const loc = useLocation()
      return <span data-testid="loc">{`${loc.pathname}${loc.search}`}</span>
    }
    render(
      <MemoryRouter>
        <SearchBox />
        <Routes>
          <Route path="*" element={<Probe />} />
        </Routes>
      </MemoryRouter>,
    )
    const form = screen.getByTestId('header-search')
    expect(form.className).toContain('flex-nowrap')
    fireEvent.change(screen.getByTestId('header-search-input'), { target: { value: '确权' } })
    fireEvent.submit(form)
    expect(screen.getByTestId('loc').textContent).toBe(`/search?q=${encodeURIComponent('确权')}`)
  })
})

// ------------------------------------------------------------ A 块：索引文件核
describe('批3 A块 · 静态索引文件（committed）', () => {
  const idx = indexJson as SearchIndexDoc

  function whitelist(): Record<string, string[]> {
    const py = whitelistPy
    const start = py.indexOf('_PUBLIC_DOCS = {')
    const out: Record<string, string[]> = {}
    let i = start
    for (const fam of ['regulation', 'whitepapers', 'papers', 'cop-library']) {
      const key = `"${fam}": (`
      const k = py.indexOf(key, i)
      let depth = 1
      let j = k + key.length
      while (depth > 0) {
        if (py[j] === '(') depth++
        else if (py[j] === ')') depth--
        j++
      }
      const block = py
        .slice(k + key.length, j - 1)
        .split('\n')
        .filter((line: string) => !line.trimStart().startsWith('#'))
        .join('\n')
      out[fam] = [...block.matchAll(/"([^"\n]+)"/g)].map((m) => m[1])
      i = j
    }
    return out
  }

  it('件数与在册公开清单一一对应（索引＝白名单，零超出）', () => {
    const wl = whitelist()
    const expected = new Set<string>()
    for (const [fam, items] of Object.entries(wl)) {
      for (const e of items) expected.add(`/docs/${fam}/${e}`)
    }
    const actual = new Set(
      idx.entries
        .filter((e) => e.family !== '术语' && e.family !== '栏目')
        .map((e) => e.url),
    )
    expect(actual.size).toBe(expected.size)
    for (const u of expected) expect(actual.has(u), `索引缺 ${u}`).toBe(true)
    expect(idx.counts['术语']).toBe(151)
  })

  it('编号形态零命中（title／summary／keywords；禁 COP-数字·GSEQ-数字·A-数字·T-三位·base_protocol）', () => {
    const forbidden = [/\bCOP-\d+\b/i, /\bGSEQ-\d+\b/, /(^|[^A-Z0-9])A-\d+(?![0-9])/, /\bT-\d{3}\b/, /base_protocol/i]
    for (const e of idx.entries) {
      for (const f of [e.title, e.summary] as const) {
        for (const re of forbidden) expect(re.test(f), `${e.title.slice(0, 30)} :: ${f.slice(0, 40)}`).toBe(false)
      }
      for (const kw of e.keywords) {
        for (const re of forbidden) expect(re.test(kw), `keyword ${kw}`).toBe(false)
      }
    }
  })

  it('每条带族／数据性质／时间（generated_at）／url', () => {
    expect(idx.generated_at).toMatch(/^\d{4}-\d{2}-\d{2}T/)
    const families = new Set(['制度', '白皮书', '论文', '素材', '术语', '栏目'])
    for (const e of idx.entries) {
      expect(families.has(e.family), e.title).toBe(true)
      expect(['real', 'simulated', 'synthetic']).toContain(e.nature)
      expect(e.url.startsWith('/')).toBe(true)
    }
  })

  it('栏目页 ⊆ PAGE_META 公开项', () => {
    const meta = new Set<string>()
    for (const m of pagesSrc.matchAll(/\{ path: '([^']+)', title: '[^']*', layer: '[^']*', dataSource: '[^']*', permission: '([^']*)', description: '[^']*' \},?/g)) {
      if (m[1].includes(':')) continue
      if (!m[2].includes('公开')) continue
      if (m[1] === '/auth' || m[1] === '/register') continue
      meta.add(m[1])
    }
    const columns = idx.entries.filter((e) => e.family === '栏目')
    expect(columns.length).toBeGreaterThan(0)
    for (const c of columns) expect(meta.has(c.url), `栏目越界 ${c.url}`).toBe(true)
  })
})

// ------------------------------------------------------------ B 块：货架三卡
describe('批3 B块 · 公开货架三卡三态', () => {
  it('每卡五项齐（名称／用途／数据性质／获取方式／状态＋日期），三态视觉可区分', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 404, json: async () => ({ detail: 'not found' }) }) as Response))
    render(
      <MemoryRouter>
        <ToolshelfPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('toolshelf-cards')).toBeTruthy())
    const ok = screen.getByTestId('tool-card-ok')
    expect(ok.textContent).toContain('自助验链')
    expect(ok.textContent).toContain('输入件名与哈希，自助核验公开件在册状态与链上留痕。')
    expect(ok.textContent).toContain('真实')
    expect(ok.textContent).toContain('可用')
    expect(ok.textContent).toContain('打开工具')
    expect(ok.textContent).toContain('更新 2026-10-28')
    const dev = screen.getByTestId('tool-card-dev')
    expect(dev.textContent).toContain('全站检索')
    expect(dev.textContent).toContain('在建')
    expect(dev.textContent).toContain('上线后可用')
    const off = screen.getByTestId('tool-card-off')
    expect(off.textContent).toContain('旧版演示脚本')
    expect(off.textContent).toContain('下架')
    expect(off.textContent).toContain('暂不可用')
    expect(off.textContent).toContain('下架 2026-10-20')
    // 三态样式可区分（徽标类不同）
    const badgeOf = (el: HTMLElement) => Array.from(el.querySelectorAll('span')).map((s) => s.className).join('|')
    expect(badgeOf(ok)).not.toBe(badgeOf(dev))
    expect(badgeOf(dev)).not.toBe(badgeOf(off))
    // 只做呈现：卡区明示上架权归属（operator 提＋创始人核）
    expect(screen.getByTestId('toolshelf-cards').textContent).toContain('本区只做呈现与状态位')
  })
})

// ------------------------------------------------------------ C 块：公告两态
describe('批3 C块 · 公告列表与撤回灰态', () => {
  const LIST_WITH_WITHDRAWN = {
    count: 2,
    announcements: [
      {
        announcement_id: 'AN-1',
        title: '素材库对外版分批开放：批 A 已上线',
        body: '对外版剥除注册号头、标注数据性质与来源；批 B/C 已合并入仓，部署另行公告。',
        published_at: '2026-10-27 18:00',
      },
      {
        announcement_id: 'AN-2',
        title: '夜间维护暂停访问通知',
        body: '原定夜间维护安排。',
        published_at: '2026-10-22 22:00',
        withdrawn_at: '2026-10-22 21:40',
        withdrawn_reason: '维护改期，原公告作废',
      },
    ],
    note: '公告栏（对外公告区）',
  }

  function mockAnnouncements(payload: unknown) {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      const u = String(url)
      if (u.includes('/api/v1/announcements/list')) {
        return { ok: true, status: 200, json: async () => envelope(payload) } as Response
      }
      return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
    }))
  }

  it('已撤回灰态：标题置灰前缀、原发与撤回双时间戳（含原因）', async () => {
    mockAnnouncements(LIST_WITH_WITHDRAWN)
    render(
      <MemoryRouter>
        <AnnouncementsPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('ann-withdrawn')).toBeTruthy())
    const w = screen.getByTestId('ann-withdrawn')
    expect(w.textContent).toContain('［已撤回］')
    expect(w.textContent).toContain('原发 2026-10-22 22:00')
    expect(w.textContent).toContain('撤回 2026-10-22 21:40')
    expect(w.textContent).toContain('维护改期，原公告作废')
    expect(w.className).toContain('opacity-60')
    // 正常条目双时间戳不串
    const normal = screen.getByTestId('ann-item')
    expect(normal.textContent).toContain('2026-10-27 18:00')
    expect(normal.textContent).not.toContain('撤回')
  })

  it('首页公告条：有公告 → 一行高（h-9）渲染；空 → 不渲染不占首屏', async () => {
    mockAnnouncements(LIST_WITH_WITHDRAWN)
    render(
      <MemoryRouter>
        <HomeNoticeBar />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('home-notice')).toBeTruthy())
    expect(screen.getByTestId('home-notice').className).toContain('h-9')
    expect(screen.getByTestId('home-notice').textContent).toContain('素材库对外版分批开放')
    expect(screen.getByTestId('home-notice').textContent).toContain('2026-10-27')
  })

  it('首页公告条：空栏 → null（空态呈现）', async () => {
    mockAnnouncements({ count: 0, announcements: [], note: '公告栏（对外公告区）' })
    render(
      <MemoryRouter>
        <HomeNoticeBar />
      </MemoryRouter>,
    )
    await act(async () => {
      await new Promise((r) => setTimeout(r, 50))
    })
    expect(screen.queryByTestId('home-notice')).toBeNull()
  })
})
