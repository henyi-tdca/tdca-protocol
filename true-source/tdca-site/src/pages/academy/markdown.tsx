// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 商学院栏目静态文档渲染器（L1SI152-EDU-PORTAL-001）
// 约束矩阵: 交办令 §三/§九——原文照贴、零改写；本渲染器 ⛔ 不改一字，仅做块级映射
// 支持子集: #/##/### 标题（页面内降一档）、表格、有序/无序列表、引用、--- 分隔、**粗体** 行内
// =============================================================================
import type { ReactNode } from 'react'

/** 行内：仅 **粗体** 语法（附件已实测不含链接/图片/代码块） */
export function mdInline(text: string): ReactNode {
  const parts = text.split('**')
  if (parts.length === 1) return text
  return parts.map((p, i) => (i % 2 === 1 ? <strong key={i}>{p}</strong> : <span key={i}>{p}</span>))
}

interface TableBlock {
  kind: 'table'
  header: string[]
  rows: string[][]
}
interface ListBlock {
  kind: 'list'
  ordered: boolean
  items: string[]
}
interface QuoteBlock {
  kind: 'quote'
  lines: string[]
}
interface HeadingBlock {
  kind: 'heading'
  level: number
  text: string
}
interface ParaBlock {
  kind: 'para'
  text: string
}
type Block = TableBlock | ListBlock | QuoteBlock | HeadingBlock | ParaBlock

/** 块级解析：文本节点原样透传（⛔ 不改一字） */
export function mdBlocks(md: string): Block[] {
  const lines = md.split(/\r?\n/)
  const blocks: Block[] = []
  let i = 0
  while (i < lines.length) {
    const ln = lines[i]
    if (!ln.trim()) {
      i += 1
      continue
    }
    if (/^\s*---+\s*$/.test(ln)) {
      i += 1
      continue // 分隔线：版面由页面样式承担，不渲染
    }
    const h = ln.match(/^(#{1,3})\s+(.*)$/)
    if (h) {
      blocks.push({ kind: 'heading', level: h[1].length, text: h[2].replace(/\*\*/g, '') })
      i += 1
      continue
    }
    if (ln.trimStart().startsWith('|')) {
      const raw: string[] = []
      while (i < lines.length && lines[i].trimStart().startsWith('|')) {
        raw.push(lines[i])
        i += 1
      }
      const cells = (row: string) =>
        row
          .trim()
          .replace(/^\|/, '')
          .replace(/\|$/, '')
          .split('|')
          .map((c) => c.trim())
      const kept = raw.filter((r) => !/^\s*\|[\s\-|:]+\|\s*$/.test(r))
      if (kept.length > 0) {
        blocks.push({ kind: 'table', header: cells(kept[0]), rows: kept.slice(1).map(cells) })
      }
      continue
    }
    const ol = ln.match(/^\s*\d+\.\s+(.*)$/)
    const ul = ln.match(/^\s*-\s+(.*)$/)
    if (ol || ul) {
      const ordered = Boolean(ol)
      const items: string[] = []
      while (i < lines.length) {
        const m = lines[i].match(ordered ? /^\s*\d+\.\s+(.*)$/ : /^\s*-\s+(.*)$/)
        if (!m) break
        items.push(m[1])
        i += 1
      }
      blocks.push({ kind: 'list', ordered, items })
      continue
    }
    if (ln.trimStart().startsWith('>')) {
      const qlines: string[] = []
      while (i < lines.length && lines[i].trimStart().startsWith('>')) {
        qlines.push(lines[i].trimStart().replace(/^>\s?/, ''))
        i += 1
      }
      blocks.push({ kind: 'quote', lines: qlines })
      continue
    }
    // 段落：合并到下一个空行
    const para = [ln]
    i += 1
    while (i < lines.length && lines[i].trim() && !/^(#{1,3}\s|\||>|---|\s*(-|\d+\.)\s)/.test(lines[i])) {
      para.push(lines[i])
      i += 1
    }
    blocks.push({ kind: 'para', text: para.join(' ') })
  }
  return blocks
}

/** 渲染：标题降一档（页面自身 h1 占顶），表格横向滚动（移动端适配） */
export function MarkdownDoc({ md }: { md: string }) {
  const blocks = mdBlocks(md)
  return (
    <article data-testid="biz-doc" className="space-y-4 text-sm leading-6 text-gray-700">
      {blocks.map((b, idx) => {
        switch (b.kind) {
          case 'heading': {
            const Tag = ([ 'h2', 'h3', 'h4' ] as const)[Math.min(b.level - 1, 2)]
            const cls =
              b.level === 1
                ? 'text-xl font-bold text-gray-900 pt-2'
                : b.level === 2
                  ? 'text-lg font-bold text-gray-900 pt-2'
                  : 'text-base font-semibold text-gray-800 pt-1'
            return (
              <Tag key={idx} className={cls}>
                {mdInline(b.text)}
              </Tag>
            )
          }
          case 'para':
            return (
              <p key={idx} className="whitespace-pre-wrap">
                {mdInline(b.text)}
              </p>
            )
          case 'quote':
            return (
              <blockquote key={idx} className="rounded-md border-l-4 border-gray-300 bg-gray-50 px-3 py-2 text-xs text-gray-600 space-y-1">
                {b.lines.map((q, j) => (
                  <p key={j}>{mdInline(q)}</p>
                ))}
              </blockquote>
            )
          case 'list':
            return b.ordered ? (
              <ol key={idx} className="list-decimal space-y-1 pl-6">
                {b.items.map((it, j) => (
                  <li key={j}>{mdInline(it)}</li>
                ))}
              </ol>
            ) : (
              <ul key={idx} className="list-disc space-y-1 pl-6">
                {b.items.map((it, j) => (
                  <li key={j}>{mdInline(it)}</li>
                ))}
              </ul>
            )
          case 'table':
            return (
              <div key={idx} className="overflow-x-auto">
                <table className="w-full min-w-[36rem] border-collapse text-sm">
                  <thead>
                    <tr>
                      {b.header.map((cell, j) => (
                        <th key={j} className="border border-gray-200 bg-gray-50 px-3 py-2 text-left font-semibold text-gray-800">
                          {mdInline(cell)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {b.rows.map((row, ri) => (
                      <tr key={ri}>
                        {row.map((cell, ci) => (
                          <td key={ci} className="border border-gray-200 px-3 py-2 align-top">
                            {mdInline(cell)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
        }
      })}
    </article>
  )
}
