// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F1 存证自查入口 M1″（031 令 A-24 页面标注验收）
// 约束矩阵: L1SI154-031 §四（标注原文不得省）+ §六 验收 7（页面含标注原文）
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { AuditPage } from '@/pages/audit'

function envelope(payload: unknown) {
  return { data: payload, nca_watermark: 'sha256:test', ts: '2026-08-12T00:00:00Z', data_nature: 'simulated' }
}

beforeEach(() => {
  localStorage.clear()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('M1″ 存证自查（031 令页面标注）', () => {
  it('audit 页含自查块与 §四 标注原文（不得省）', async () => {
    const fn = vi.fn(async (url: string) => {
      if (url.includes('/api/v1/audit/ledger-public')) {
        return { ok: true, status: 200, json: async () => envelope({ events: [], total: 0, note: '' }) } as Response
      }
      throw new Error(`unexpected url ${url}`)
    })
    vi.stubGlobal('fetch', fn)
    render(<AuditPage />)
    // 031 令 §四 标注原文（逐字）
    expect(screen.getByText(/本查询可证：该条记录存在于台账，且其内容与写入时一致；/)).toBeTruthy()
    expect(screen.getByTestId('selfcheck-input')).toBeTruthy()
    expect(screen.getByTestId('selfcheck-run')).toBeTruthy()
  })

  it('查询成功渲染十字段；未查到渲染 fail-closed（不渲染 actor 原值）', async () => {
    const record = {
      nca_id: 'NCA-WEB-test0001', action: 'TEST_ACT', ts: '2026-10-19T00:00:00Z',
      artifact_filename_sha256_16: 'AB12CD34EF56GH78', artifact_ext: 'md',
      sha256_8: 'abcd1234',
      rec_hash: 'ABCD1234EFGH5678', prev_hash: 'MISSING',
      detached: 1, detach_reason: 'missing_predecessor',
      actor_hash: '0a1b2c3d',
    }
    const fn = vi.fn(async (url: string) => {
      if (url.includes('/api/v1/audit/ledger-public')) {
        return { ok: true, status: 200, json: async () => envelope({ events: [], total: 0, note: '' }) } as Response
      }
      if (url.includes('/api/v1/selfcheck/nca/NCA-WEB-test0001')) {
        return {
          ok: true, status: 200,
          json: async () => envelope({
            record, rec_hash_spec: 'rec_hash = sha256(...)',
            page_disclaimer: '本查询可证：…',
            note: '只读自查；⛔ 响应不含 actor 原值/凭据/内部编号/台账件名原值；⛔ 不构成对外证明（存证对外可验证性之宣称，另候明示）',
          }),
        } as Response
      }
      throw new Error(`unexpected url ${url}`)
    })
    vi.stubGlobal('fetch', fn)
    render(<AuditPage />)
    fireEvent.change(screen.getByTestId('selfcheck-input'), { target: { value: 'NCA-WEB-test0001' } })
    fireEvent.click(screen.getByTestId('selfcheck-run'))
    await waitFor(() => expect(screen.getByTestId('selfcheck-record')).toBeTruthy())
    expect(screen.getByText('missing_predecessor')).toBeTruthy()
    // 035-A2 令 B 项：硬注取 API note 渲染（一源两现同字，⛔ 前端另行手写）
    expect(screen.getByTestId('selfcheck-note').textContent).toContain('不构成对外证明')
    expect(screen.getByText(/件名校验码 AB12CD34EF56GH78/)).toBeTruthy()
  })
})
