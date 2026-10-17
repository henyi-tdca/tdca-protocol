// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI152-EDU-PORTAL-001 商学院两页自检四验
// 约束矩阵: 交办令 §三（原文照贴·零内部编号·价格留白·不加外链）§九（⛔ 不改一字）
//  验①哈希：两 ?raw 源 sha256_16 == 在册值（9C9E83BACC40E70F ／ 3C5F8F33511F53AB）
//  验②逐句照贴：对源逐行剥 markdown 语法后断言出现在渲染 textContent（零丢句）
//  验③渲染：h1 与 meta.title 同名、关键句在位、两页互链
//  验④零编号零金额零外链：渲染文本不含内部编号/金额模式/链接元素
// =============================================================================
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect } from 'vitest'
import { BizSchoolIntroPage, BizSchoolOutlinePage } from '@/pages/academy/biz-school'
import introMd from '@/pages/academy/biz-intro.md?raw'
import outlineMd from '@/pages/academy/outline.md?raw'

/** WebCrypto 标准接口（零新依赖；与 node:crypto 同为 SHA-256） */
async function sha16(s: string) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s))
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase()
    .slice(0, 16)
}

/** 逐句照贴守卫：剥掉 markdown 语法后的正文句子必须全部出现在渲染文本里 */
function expectEverySourceLine(rendered: string, md: string, label: string) {
  const missing: string[] = []
  const lines = md.split(/\r?\n/)
  for (const raw of lines) {
    const t = raw.trim()
    if (!t) continue
    if (/^---+\s*$/.test(t)) continue // 分隔线不渲染
    // 剥语法：标题符/列表符/引用符/表格线/加粗标记
    let s = t
      .replace(/^#{1,6}\s+/, '')
      .replace(/^>\s?/, '')
      .replace(/^\s*(?:[-*]|\d+\.)\s+/, '')
      .replace(/\*\*/g, '')
      .replace(/`/g, '')
    // 表格行：剥首尾竖线后逐格断言
    if (s.startsWith('|')) {
      s = s.replace(/^\|/, '').replace(/\|\s*$/, '')
      if (/^[\s\-|:]+$/.test(s)) continue // 表头分隔行
      for (const cell of s.split('|')) {
        const c = cell.trim()
        if (c) checkLine(c)
      }
      continue
    }
    checkLine(s)

    function checkLine(plain: string) {
      // 渲染文本里的空白可能归一（块级 join），反引号照透传故两侧同剥；归一后包含断言
      const norm = (x: string) => x.replace(/`/g, '').replace(/\s+/g, ' ').trim()
      if (!norm(rendered).includes(norm(plain))) missing.push(`${label}: ${plain}`)
    }
  }
  expect(missing).toEqual([])
}

describe('L1SI152-EDU-PORTAL-001 商学院两页自检四验', () => {
  it('验① 哈希：两附件 ?raw 源与在册 sha256_16 一致（零改写）', async () => {
    expect(await sha16(introMd)).toBe('9C9E83BACC40E70F')
    expect(await sha16(outlineMd)).toBe('3C5F8F33511F53AB')
  })

  it('验②③ /academy 介绍页：h1、关键句、逐句照贴、链到目录页', () => {
    render(
      <MemoryRouter>
        <BizSchoolIntroPage />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('TDCA 商学院')
    const page = screen.getByTestId('biz-school-intro')
    expect(page).toHaveTextContent('不是来讲课的')
    expect(page).toHaveTextContent('五卷')
    expect(page).toHaveTextContent('35')
    expect(page).toHaveTextContent('入学即上岗')
    expect(screen.getByRole('link', { name: /教材目录（纲要）/ })).toHaveAttribute('href', '/academy/outline')
    expectEverySourceLine(page.textContent ?? '', introMd, 'intro')
  })

  it('验②③ /academy/outline 目录页：h1、关键句、逐句照贴、返回介绍页', () => {
    render(
      <MemoryRouter>
        <BizSchoolOutlinePage />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('教材目录（纲要）')
    const page = screen.getByTestId('biz-school-outline')
    expect(page).toHaveTextContent('五卷')
    expect(page).toHaveTextContent('制度哲学')
    expect(page).toHaveTextContent('入门本')
    expect(screen.getByRole('link', { name: /返回商学院介绍/ })).toHaveAttribute('href', '/academy')
    expectEverySourceLine(page.textContent ?? '', outlineMd, 'outline')
  })

  it('验④ 零内部编号／零金额／零外链：两页渲染文本干净', () => {
    const { container: c1 } = render(
      <MemoryRouter>
        <BizSchoolIntroPage />
      </MemoryRouter>,
    )
    const { container: c2 } = render(
      <MemoryRouter>
        <BizSchoolOutlinePage />
      </MemoryRouter>,
    )
    for (const [name, c] of [ ['intro', c1], ['outline', c2] ] as const) {
      const text = c.textContent ?? ''
      expect(text).not.toMatch(/GSEQ-\d+/)
      expect(text).not.toMatch(/\bNCA-\d{3}\b/)
      expect(text).not.toMatch(/\bT-\d{3}\b/)
      expect(text).not.toMatch(/\bL1SI\d+/)
      expect(text).not.toMatch(/[¥￥]\s?\d/)
      expect(text).not.toMatch(/\$\d/)
      // 不加外链：页内不得有 <a> 指向站外
      const anchors = Array.from(c.querySelectorAll('a'))
      for (const a of anchors) {
        const href = a.getAttribute('href') ?? ''
        expect(href.startsWith('/'), `${name} 出现站外链接: ${href}`).toBe(true)
      }
    }
  })
})
