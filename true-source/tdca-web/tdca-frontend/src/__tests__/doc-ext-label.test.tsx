// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: SITEGO-002 段B 自测（L1SI231）
// 约束矩阵: 表外三件状态标签落文档详情页呈现——词面逐字照
//   TDCA-RULING-L1SI231-MAILBOX-001（⛔自拟⛔加减字）；⛔新增地图行、⛔改制表字段、
//   ⛔改件面、⛔接口；负向：白名单外件无标。
// =============================================================================
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { afterEach, describe, expect, it } from 'vitest'
import { DocDetailPage } from '@/pages/docs'

function stubFetch(filename: string) {
  const stub = {
    family: 'regulation',
    slug: filename,
    filename,
    display_name: filename,
    version: 'V1.0',
    bytes: 24,
    sha256: 'ab'.repeat(32),
    sha256_16: 'AB' + 'ab'.repeat(30),
    content: '第一条 正文首段：测试件内容。',
  }
  const orig = window.fetch
  window.fetch = (() => Promise.resolve(new Response(JSON.stringify(stub), { status: 200 }))) as typeof window.fetch
  return orig
}

function renderDetail(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/docs/:family/:slug" element={<DocDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

afterEach(() => {
  // @ts-expect-error 还原打桩
  window.fetch = undefined
})

describe('SITEGO-002 段B：表外三件状态标签（文档页呈现）', () => {
  const CASES: Array<[string, string, string]> = [
    // [slug（URL 形态）, 文件名, 期望词面]
    ['人机协作工作条例', '人机协作工作条例.md', '现行'],
    ['业务端节点接入与同构契约条例（对外公开版·V1.0）', '业务端节点接入与同构契约条例（对外公开版·V1.0）.md', '现行'],
    ['配置权市场授权追认附记', '配置权市场授权追认附记.md', '现行（凭证）'],
  ]
  for (const [slug, filename, label] of CASES) {
    it(`带 .md 索引链形态：${slug} → 徽标「${label}」逐字`, async () => {
      const orig = stubFetch(filename)
      renderDetail(`/docs/regulation/${encodeURIComponent(slug)}.md`)
      await waitFor(() => expect(screen.getByTestId('doc-body')).toBeTruthy())
      const badge = screen.getByTestId('doc-ext-label')
      expect(badge.textContent).toBe(label)
      window.fetch = orig
    })
    it(`裸 slug 直访形态：${slug} → 同命中`, async () => {
      const orig = stubFetch(filename)
      renderDetail(`/docs/regulation/${encodeURIComponent(slug)}`)
      await waitFor(() => expect(screen.getByTestId('doc-body')).toBeTruthy())
      expect(screen.getByTestId('doc-ext-label').textContent).toBe(label)
      window.fetch = orig
    })
  }
  it('负向：白名单外件（流程环节卡发现）无徽标', async () => {
    const orig = stubFetch('流程环节卡发现（五问·六类失败·第4张卡）.md')
    renderDetail(`/docs/regulation/${encodeURIComponent('流程环节卡发现（五问·六类失败·第4张卡）')}.md`)
    await waitFor(() => expect(screen.getByTestId('doc-body')).toBeTruthy())
    expect(screen.queryByTestId('doc-ext-label')).toBeNull()
    window.fetch = orig
  })
})
