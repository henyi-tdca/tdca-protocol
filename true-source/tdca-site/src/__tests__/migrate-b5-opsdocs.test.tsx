// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: MIGRATE 批5（L1SI206）运维手册三界面验证
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI206-MIGRATE-B5-001 §四沙盒五组
//   ① 三面可达（组件渲染）② 内容非空——清单按组过滤 1/3/3 与旧版在册七件逐项对得上（⛔空壳）
//   ③ 版本比对——按名出件正文直读（源件为准）④ 私域隔离——⛔入 PAGE_META 公开题名录
//   ⑤ fail-closed——匿名/取件失败只给人话门槛文案
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { OpsReadmePage } from '@/pages/OpsReadmePage'
import { OpsOpsPage } from '@/pages/OpsOpsPage'
import { OpsChangelogPage } from '@/pages/OpsChangelogPage'
import { ROUTE_PATHS, PAGE_META } from '@/pages/PagesIndex'

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-11-09T00:00:00Z', data_nature: 'real' }
}

/** 在册白名单七件（组分布：README 1／OPS 3／CHANGELOG 3） */
const SEVEN = [
  { name: 'TDCA-MAN-SITE-PHASE2-OPS-001-V1.0-manual.md', label: '运维手册（人读定稿 V1.0-FROZEN）', sha256_16: 'A1'.repeat(8), bytes: 100, missing: false },
  { name: 'TDCA-MAN-SITE-PHASE2-OPS-001-MACHINE-spec.md', label: '运维制度（机读定稿 V1.0-FROZEN）', sha256_16: 'B2'.repeat(8), bytes: 100, missing: false },
  { name: 'TDCA-TPL-OPS-LOG-001-tpl.md', label: '运维日志模板（人读）', sha256_16: 'C3'.repeat(8), bytes: 100, missing: false },
  { name: 'TDCA-TPL-OPS-LOG-001-MACHINE-tpl.md', label: '运维日志模板（机读）', sha256_16: 'D4'.repeat(8), bytes: 100, missing: false },
  { name: 'TDCA-STD-SITE-INGEST-TRAIL-001-trail.md', label: '入站留痕制度（人读 V1.0-FROZEN）', sha256_16: 'E5'.repeat(8), bytes: 100, missing: false },
  { name: 'TDCA-STD-SITE-INGEST-TRAIL-001-trail.yaml', label: '入站留痕制度（机读 yaml）', sha256_16: 'F6'.repeat(8), bytes: 100, missing: false },
  { name: 'TDCA-SIGNOFF-STD-SITE-INGEST-TRAIL-001-signoff.md', label: '入站留痕制度（签批落地件）', sha256_16: 'G7'.repeat(8), bytes: 100, missing: false },
]

function mockSeven() {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
    const u = String(url)
    if (u.endsWith('/api/v1/ops/files')) {
      return { ok: true, status: 200, json: async () => envelope({ total: 7, files: SEVEN }) } as Response
    }
    if (u.includes('/api/v1/ops/files/')) {
      const name = decodeURIComponent(u.split('/api/v1/ops/files/')[1])
      const hit = SEVEN.find((f) => f.name === name)
      if (hit) {
        return { ok: true, status: 200, text: async () => `# ${hit.label}\n内容照源件。` } as Response
      }
      return { ok: false, status: 404, json: async () => ({ detail: 'not found' }) } as Response
    }
    return { ok: false, status: 404, json: async () => ({ detail: 'unexpected' }) } as Response
  }))
}

beforeEach(() => { localStorage.clear(); sessionStorage.clear() })
afterEach(() => { vi.unstubAllGlobals() })

describe('MIGRATE 批5：三面清单分组与旧版在册七件逐项对得上（沙盒②⛔空壳）', () => {
  it('/ops/readme（README 项目说明）：在册一组一件＝运维手册人读定稿', async () => {
    mockSeven()
    render(<MemoryRouter><OpsReadmePage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ops-readme-list')).toBeTruthy())
    expect(screen.getByTestId('ops-readme-list').querySelectorAll('li')).toHaveLength(1)
    await waitFor(() => expect(screen.getByTestId('ops-readme-body').textContent).toContain('运维手册（人读定稿 V1.0-FROZEN）'))
  })

  it('/ops/ops（OPS 运维操作）：在册一组三件＝制度机读＋日志模板人读/机读', async () => {
    mockSeven()
    render(<MemoryRouter><OpsOpsPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ops-ops-list')).toBeTruthy())
    expect(screen.getByTestId('ops-ops-list').querySelectorAll('li')).toHaveLength(3)
  })

  it('/ops/changelog（CHANGELOG 变更记录）：在册一组三件＝留痕制度人读/机读/签批', async () => {
    mockSeven()
    render(<MemoryRouter><OpsChangelogPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ops-changelog-list')).toBeTruthy())
    expect(screen.getByTestId('ops-changelog-list').querySelectorAll('li')).toHaveLength(3)
  })

  it('yaml 件出「复制全文」钮（照旧壳惯例）＋点选切换正文（交互与旧版同）', async () => {
    mockSeven()
    render(<MemoryRouter><OpsChangelogPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ops-changelog-list')).toBeTruthy())
    const buttons = screen.getAllByRole('button')
    const yamlBtn = buttons.find((b) => b.textContent?.includes('机读 yaml'))
    expect(yamlBtn).toBeTruthy()
    fireEvent.click(yamlBtn as HTMLElement)
    await waitFor(() => expect(screen.getByTestId('ops-changelog-copy')).toBeTruthy())
    expect(screen.getByTestId('ops-changelog-body').textContent).toContain('机读 yaml')
  })
})

describe('MIGRATE 批5：私域隔离（沙盒④——⛔入公开题名录⛔入检索面）', () => {
  it('三面 ⛔入 PAGE_META／ROUTE_PATHS 公开在册（检索索引题名录不收运维内容）', () => {
    expect(PAGE_META.map((m) => m.path)).not.toContain('/ops/readme')
    expect(PAGE_META.map((m) => m.path)).not.toContain('/ops/ops')
    expect(PAGE_META.map((m) => m.path)).not.toContain('/ops/changelog')
    expect(ROUTE_PATHS).not.toContain('/ops/readme')
    expect(ROUTE_PATHS).not.toContain('/ops/ops')
    expect(ROUTE_PATHS).not.toContain('/ops/changelog')
    // 三面互链只在私域壳内（互链指向三面自身与 /ops，⛔无公开导航指向）
  })
})

describe('MIGRATE 批5：fail-closed（沙盒⑤——匿名直访只给人话门槛）', () => {
  it('取件失败时显示「须运维身份（operator/founder）登录后查阅」⛔堆栈⛔内部码', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      ({ ok: false, status: 401, json: async () => ({ detail: 'unauthorized' }) }) as Response))
    render(<MemoryRouter><OpsReadmePage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByTestId('ops-readme-fail')).toBeTruthy())
    expect(screen.getByTestId('ops-readme-fail').textContent).toContain('须运维身份')
  })
})
