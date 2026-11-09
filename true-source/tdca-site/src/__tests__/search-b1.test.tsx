// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-SITE-001 | 目标函数: MIGRATE 批1 — 检索产线测试（排序档位／AND 语义／
//          高亮切分／装载 fail-closed／检索页两态）
// 约束矩阵: L1SI206 MIGRATE-B1-001 §二.4（增对应测试：新测试过＋全量仍全绿）
// SPDX-License-Identifier: TDCA-Internal
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import {
  loadSearchIndex,
  searchEntries,
  splitForHighlight,
  __resetSearchIndexCacheForTest,
  type SearchIndexEntry,
} from '@/lib/search-index'
import { SearchPage } from '@/pages/SearchPage'

function entry(partial: Partial<SearchIndexEntry> & { title: string }): SearchIndexEntry {
  return {
    family: '制度',
    summary: '',
    keywords: [],
    url: '/docs/regulation/x.md',
    version: '',
    nature: 'real',
    body: '',
    ...partial,
  }
}

beforeEach(() => {
  localStorage.clear()
  __resetSearchIndexCacheForTest()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('检索排序档位（标题＞摘要＞正文；同档制度族优先）', () => {
  const entries = [
    entry({ title: '甲条例', family: '论文', body: '正文含 配置权 字样' }),
    entry({ title: '乙摘要件', family: '制度', summary: '摘要含 配置权' }),
    entry({ title: '配置权 标题件', family: '素材' }),
    entry({ title: '丁同档制度', family: '制度', summary: '摘要含 配置权' }),
  ]

  it('档位降序：标题档先于摘要档先于正文档', () => {
    const r = searchEntries(entries, '配置权')
    expect(r.map((x) => x.tier)).toEqual([3, 2, 2, 1])
    expect(r[0].entry.title).toBe('配置权 标题件')
  })

  it('同档位制度族优先，其余标题升序', () => {
    const r = searchEntries(entries, '配置权')
    expect(r[1].entry.family).toBe('制度')
    expect(r[1].entry.title).toBe('丁同档制度')
  })

  it('keywords 视同摘要档', () => {
    const r = searchEntries([entry({ title: '戊', keywords: ['MARKET-CONF'] })], 'market-conf')
    expect(r).toHaveLength(1)
    expect(r[0].tier).toBe(2)
  })
})

describe('AND 语义与空白查询', () => {
  const entries = [
    entry({ title: '可信协作宪法', summary: '序言与十条' }),
    entry({ title: '智能体定义条例', summary: '二十一条' }),
  ]

  it('多术语须全部命中（AND）', () => {
    expect(searchEntries(entries, '宪法 序言')).toHaveLength(1)
    expect(searchEntries(entries, '宪法 二十一条')).toHaveLength(0)
  })

  it('空白查询返回空（⛔ 全量返回冒充命中）', () => {
    expect(searchEntries(entries, '   ')).toHaveLength(0)
    expect(searchEntries(entries, '')).toHaveLength(0)
  })
})

describe('高亮切分（长词优先／大小写不敏感／无命中原样）', () => {
  it('按术语切出命中段', () => {
    const parts = splitForHighlight('配置权市场规范', '配置权')
    expect(parts).toEqual([
      { text: '配置权', hit: true },
      { text: '市场规范', hit: false },
    ])
  })

  it('多术语长词优先且大小写不敏感', () => {
    const parts = splitForHighlight('TDCA Market Spec', 'market tdca')
    expect(parts.filter((p) => p.hit).map((p) => p.text)).toEqual(['TDCA', 'Market'])
  })

  it('无命中返回原样单段', () => {
    expect(splitForHighlight('完全无关', '配置权')).toEqual([{ text: '完全无关', hit: false }])
  })
})

describe('索引装载 fail-closed（⛔ 臆造）', () => {
  it('fetch 拒绝 → null', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('network down') }))
    expect(await loadSearchIndex()).toBeNull()
  })

  it('响应非 ok → null；成功 → doc', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 404 }) as Response))
    expect(await loadSearchIndex()).toBeNull()

    __resetSearchIndexCacheForTest()
    const doc = { spec: 'TDCA-SEARCH-INDEX-V1', generated_at: '', generated_by: '', sources: {}, counts: {}, total: 0, entries: [] }
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => doc }) as Response))
    expect(await loadSearchIndex()).toEqual(doc)
  })
})

describe('检索页两态（有结果／空结果／装载失败）', () => {
  const doc = {
    spec: 'TDCA-SEARCH-INDEX-V1',
    generated_at: '2026-11-09T00:00:00Z',
    generated_by: 'test',
    sources: {},
    counts: { 制度: 2, 白皮书: 0, 论文: 0, 素材: 0, 术语: 0, 栏目: 0 },
    total: 2,
    entries: [
      entry({ title: '可信协作宪法', summary: '对外可读版·十条与序言四支柱', url: '/docs/regulation/constitution' }),
      entry({ title: '智能体定义条例', summary: '对外版·二十一条', url: '/docs/regulation/agent' }),
    ],
  }

  function mockIndex(payload: unknown | 'fail') {
    const fn = vi.fn(async () => {
      if (payload === 'fail') throw new Error('network down')
      return { ok: true, status: 200, json: async () => payload } as Response
    })
    vi.stubGlobal('fetch', fn)
    return fn
  }

  function renderSearch(initialPath: string) {
    return render(
      <MemoryRouter initialEntries={[initialPath]}>
        <SearchPage />
      </MemoryRouter>,
    )
  }

  it('无查询词显示索引口径提示', async () => {
    mockIndex(doc)
    renderSearch('/search')
    await waitFor(() => expect(screen.getByTestId('search-hint')).toBeInTheDocument())
    expect(screen.getByTestId('search-hint').textContent).toContain('索引 2 条')
  })

  it('有结果：命中条渲染且高亮标记', async () => {
    mockIndex(doc)
    renderSearch('/search?q=宪法')
    await waitFor(() => expect(screen.getAllByTestId('search-result')).toHaveLength(1))
    expect(screen.getByTestId('search-results').textContent).toContain('命中 1 条')
    expect(screen.getByRole('mark').textContent).toBe('宪法')
  })

  it('空结果：提示＋三族浏览入口', async () => {
    mockIndex(doc)
    renderSearch('/search?q=不存在之词')
    await waitFor(() => expect(screen.getByTestId('search-empty')).toBeInTheDocument())
    expect(screen.getByText('制度')).toBeInTheDocument()
    expect(screen.getByText('论文')).toBeInTheDocument()
    expect(screen.getByText('素材')).toBeInTheDocument()
  })

  it('装载失败：fail-closed 提示，⛔ 臆造结果', async () => {
    mockIndex('fail')
    renderSearch('/search?q=宪法')
    await waitFor(() => expect(screen.getByTestId('search-fail-closed')).toBeInTheDocument())
    expect(screen.queryByTestId('search-results')).not.toBeInTheDocument()
  })
})
