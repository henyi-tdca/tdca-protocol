// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: SITE-SEO-A-001 乙-1 自测（每页独立标题）
// 约束矩阵: 页面标题与地址一致——PageShell 与文档库两路均设 document.title
// =============================================================================
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, describe, expect, it } from 'vitest'
import { Route, Routes } from 'react-router'
import { DocDetailPage } from '@/pages/docs'
import { TermsPage } from '@/pages/terms'

afterEach(() => {
  document.title = '' // 清场，防用例间互染
})

describe('SITE-SEO-A-001 乙-1：每页独立标题', () => {
  it('PageShell 页：document.title = 「页名 · TDCA」', () => {
    render(<MemoryRouter><TermsPage /></MemoryRouter>)
    expect(document.title).toBe('术语检索 · TDCA')
  })

  it('文档详情页：未载入先以地址件名占位，载入后用品名', async () => {
    // fetch 打桩：返回一件带正文与文件名的公开件
    const stub = {
      family: 'regulation',
      slug: 'SAMPLE-001（对外公开版·V1.0）.md',
      filename: 'SAMPLE-001（对外公开版·V1.0）.md',
      display_name: 'SAMPLE-001',
      version: 'V1.0',
      bytes: 24,
      sha256: 'ab'.repeat(32),
      sha256_16: 'AB' + 'ab'.repeat(30),
      content: '第一条 正文首段：测试件内容。',
    }
    const orig = window.fetch
    window.fetch = (() => Promise.resolve(new Response(JSON.stringify(stub), { status: 200 }))) as typeof window.fetch
    render(
      <MemoryRouter initialEntries={['/docs/regulation/SAMPLE-001%EF%BC%88%E5%AF%B9%E5%A4%96%E5%85%AC%E5%BC%80%E7%89%88%C2%B7V1.0%EF%BC%89.md']}>
        <Routes>
          <Route path="/docs/:family/:slug" element={<DocDetailPage />} />
        </Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByTestId('doc-body')).toBeTruthy())
    expect(document.title).toBe('SAMPLE-001（对外公开版·V1.0） · 文档库 · TDCA')
    window.fetch = orig
  })
})
