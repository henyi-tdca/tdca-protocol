// =============================================================================
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI162-RULES-MAP-001 /rules 制度地图自检
// 约束矩阵: 交办令 §六 R-1~R-7（计数以程序统计为准，⛔ 目测）
//  验①哈希：?raw 机读表 sha256_16 == 在册值 4BE2B6E63824DA4A（V6.4-GENESIS-EVID·R1-001-A 实测刷新）
//  验②解析：59 项；五态 30/17/5/4/3/0；五类 21/17/9/5/7；六步 7/27/17/26/2/3；
//           page_visible=false 恰 2（相遇 V0.9）；V1.0-FROZEN 恰 9（三族）；in_public 45
//  验③渲染：R-1 主表 57＋折叠 2；R-4 对外候选 4 件逐条未标生效；R-5 三族注明在位；
//           R-6 折叠区注「以生效版为准」；R-7 S5/S6 点步出「待补」横幅
// =============================================================================
import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, it, expect } from 'vitest'
import { RulesMapPage } from '@/pages/rules/rules'
import { parseDocMapItems, DOC_MAP_STATE_ORDER, DOC_MAP_CLASS_ORDER } from '@/pages/rules/parse'
import docMapYaml from '@/pages/rules/doc-map-rules.yaml?raw'

/** WebCrypto 标准接口（零新依赖；与 node:crypto 同为 SHA-256） */
async function sha16(s: string) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s))
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase()
    .slice(0, 16)
}

const ITEMS = parseDocMapItems(docMapYaml)

function renderPage() {
  return render(
    <MemoryRouter>
      <RulesMapPage />
    </MemoryRouter>,
  )
}

describe('验①② 机读表哈希与解析（R-2/R-3 程序统计）', () => {
  it('?raw 源 sha256_16 == 在册值', async () => {
    expect(await sha16(docMapYaml)).toBe('4BE2B6E63824DA4A')
  })

  it('59 项 integrity 自洽（bytes>0、sha256_16 16 位大写、in_repo 全真）', () => {
    expect(ITEMS).toHaveLength(59)
    for (const i of ITEMS) {
      expect(i.bytes).toBeGreaterThan(0)
      expect(i.sha256_16).toMatch(/^[0-9A-F]{16}$/)
      expect(i.in_repo).toBe(true)
    }
  })

  it('五态计数 30/17/5/4/3/0（R-2）', () => {
    for (const s of DOC_MAP_STATE_ORDER) {
      const n = ITEMS.filter((i) => i.state === s).length
      const want = { 生效: 30, 指引性: 17, 草案: 5, 对外候选: 4, 非制度件: 3, 待辨: 0 }[s]
      expect(n, `state=${s}`).toBe(want)
    }
  })

  it('五类计数 21/17/9/5/7（R-3）', () => {
    for (const c of DOC_MAP_CLASS_ORDER) {
      const n = ITEMS.filter((i) => i.class === c).length
      const want = { 条例: 21, 标准与流程: 17, 规范与细则: 9, 模板与表单: 5, 基本制度: 7 }[c]
      expect(n, `class=${c}`).toBe(want)
    }
  })

  it('折叠 2 恰为相遇 V0.9；注明适用件恰 9；in_public 45', () => {
    const hidden = ITEMS.filter((i) => !i.page_visible)
    expect(hidden).toHaveLength(2)
    for (const h of hidden) expect(h.filename).toContain('V0.9-DRAFT')
    const frozen = ITEMS.filter((i) => i.version === 'V1.0-FROZEN')
    expect(frozen).toHaveLength(10) // 9 件三族 DRAFT 面貌＋CORPUS-103 对外更正面貌
    const noteScope = frozen.filter(
      (i) =>
        i.filename.startsWith('TDCA-SPEC-CONFIGMARKET-001-') ||
        i.filename.startsWith('TDCA-SPEC-REGISTER-OF-RIGHTS-001-') ||
        i.filename.startsWith('TDCA-TEMPLATE-AUTH-001-'),
    )
    expect(noteScope).toHaveLength(9)
    expect(ITEMS.filter((i) => i.in_public)).toHaveLength(45)
  })
})

describe('验③ 渲染（R-1/R-4/R-5/R-6/R-7）', () => {
  it('R-1 主表 57 行＋折叠区 2 行', () => {
    renderPage()
    const main = screen.getByTestId('rules-main')
    expect(within(main).getAllByTestId('doc-row')).toHaveLength(57)
    const archived = screen.getByTestId('rules-archived')
    expect(within(archived).getAllByTestId('doc-row')).toHaveLength(2)
    expect(archived.textContent).toContain('以生效版为准')
  })

  it('R-4 对外候选 4 件逐条未标生效（徽标文字逐字＝表内 state）', () => {
    renderPage()
    const main = screen.getByTestId('rules-main')
    const candidates = ITEMS.filter((i) => i.state === '对外候选')
    expect(candidates).toHaveLength(4)
    for (const c of candidates) {
      const row = within(main).getAllByTestId('doc-row').find((r) => r.textContent!.includes(c.display_name))
      expect(row, c.filename).toBeTruthy()
      expect(within(row!).getByTestId('state-badge-对外候选')).toBeInTheDocument()
      expect(within(row!).queryByTestId('state-badge-生效')).toBeNull()
    }
  })

  it('R-5 三族 9 件均标生效且同条注明在位', () => {
    renderPage()
    const frozen = ITEMS.filter((i) => i.version === 'V1.0-FROZEN')
    expect(frozen.every((i) => i.state === '生效')).toBe(true)
    const notes = screen.getAllByTestId('frozen-note')
    expect(notes).toHaveLength(9)
    for (const n of notes) {
      expect(n.textContent).toContain('文件开头仍载 V0.1-DRAFT')
      expect(n.textContent).toContain('2026-10-03 签批落地件')
      expect(n.textContent).toContain('期一内部运行')
    }
  })

  it('R-6 主表无 V0.9 相遇件（注记原样含 V0.9 字样者除外）；折叠区 2 件在位', () => {
    renderPage()
    const main = screen.getByTestId('rules-main')
    const mainRows = within(main).getAllByTestId('doc-row')
    const v09rows = mainRows.filter((r) => {
      const head = r.querySelector('div')!.textContent!
      return head.includes('V0.9-DRAFT')
    })
    expect(v09rows).toHaveLength(0)
    // 相遇专章 V1.0 生效版 2 件在主表（state_note 原样含「V0.9-DRAFT」属 §二-F 原样呈现，⛔ 改写）
    const v10 = ITEMS.filter((i) => i.page_visible && i.filename.includes('STD-SCENE-ENCOUNTER') && i.filename.includes('V1.0'))
    expect(v10).toHaveLength(2)
    for (const i of v10) {
      expect(main.textContent).toContain(i.display_name)
    }
    const archived = screen.getByTestId('rules-archived')
    expect(archived.textContent).toContain('V0.9-DRAFT')
    expect(archived.textContent).toContain('以生效版为准')
  })

  it('R-7 S5/S6 点步出「待补」横幅；步筛生效', () => {
    renderPage()
    const nav = screen.getByTestId('step-nav')
    const s5 = within(nav).getByRole('button', { name: /S5 结算与计税/ })
    fireEvent.click(s5)
    expect(screen.getByTestId('gap-banner').textContent).toContain('待补')
    const s5count = ITEMS.filter((i) => i.page_visible && i.steps.includes('S5')).length
    expect(s5count).toBe(2)
    expect(within(screen.getByTestId('rules-main')).getAllByTestId('doc-row')).toHaveLength(s5count)
    const s6 = within(nav).getByRole('button', { name: /S6 争议与退出/ })
    fireEvent.click(s6)
    expect(screen.getByTestId('gap-banner').textContent).toContain('待补')
    const s6count = ITEMS.filter((i) => i.page_visible && i.steps.includes('S6')).length
    expect(s6count).toBe(3)
    expect(within(screen.getByTestId('rules-main')).getAllByTestId('doc-row')).toHaveLength(s6count)
  })

  it('徽标文字与表内 state 逐字一致（全 59 件域校验）', () => {
    renderPage()
    for (const s of DOC_MAP_STATE_ORDER) {
      const n = ITEMS.filter((i) => i.state === s).length
      if (n === 0) {
        expect(screen.queryByTestId(`state-badge-${s}`)).toBeNull()
      } else {
        expect(screen.getAllByTestId(`state-badge-${s}`)).toHaveLength(n)
      }
    }
  })
})
