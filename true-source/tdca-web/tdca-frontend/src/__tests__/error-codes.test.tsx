// =============================================================================
// SPDX-License-Identifier: Apache-2.0
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI153-ERROR-CODE-001 段一前端挂码验收
// 约束矩阵: 施工令 §二.2——显示「码＋中文短句」；一处常量（errors.ts）；码与短句不分两处维护
// =============================================================================
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ERROR_CODE_TABLE, FALLBACK_ERROR_CODE, errorDisplay, isKnownCode } from '@/api/errors'
import { api, type RawEnvelope } from '@/api/client'

const mockFetch = vi.fn()

function jsonResponse(body: RawEnvelope, ok = true, status = 200) {
  return { ok, status, json: async () => body } as Response
}

beforeEach(() => {
  mockFetch.mockReset()
  vi.stubGlobal('fetch', mockFetch)
  sessionStorage.clear()
})
afterEach(() => {
  vi.unstubAllGlobals()
})

describe('错误码表 v2（errors.ts 一处常量）', () => {
  it('13 码全在册（令 §四码表逐字）', () => {
    const expected: Record<string, string> = {
      'TDCA-E-INPUT-INPUT-001': '缺少必填项：〈字段名〉',
      'TDCA-E-INPUT-INPUT-002': '〈字段名〉格式不符要求',
      'TDCA-E-IDENT-PERM-001': '请先登录',
      'TDCA-E-IDENT-STATE-001': '凭证无效或已过期，请重新取得',
      'TDCA-E-AUTHZ-PERM-001': '当前账户无权执行此操作',
      'TDCA-E-ASSET-STATE-001': '该资源不存在或尚未登记',
      'TDCA-E-STATE-STATE-002': '当前状态不允许此操作',
      'TDCA-E-STATE-STATE-003': '已提交，请勿重复操作',
      'TDCA-E-RES-RES-001': '操作过于频繁，请稍后再试',
      'TDCA-E-SETL-RES-001': '额度不足',
      'TDCA-E-EXT-EXT-001': '外部服务暂不可用，请稍后重试',
      'TDCA-E-SYS-SYS-001': '系统繁忙，请稍后再试',
      'TDCA-E-GOV-PERM-002': '本次操作被制度性拒绝（合规前置未过）',
    }
    expect(ERROR_CODE_TABLE).toEqual(expected)
  })

  it('errorDisplay：在册码→短句＋码；未知码→兜底系统繁忙码', () => {
    expect(errorDisplay('TDCA-E-IDENT-PERM-001')).toBe('请先登录（TDCA-E-IDENT-PERM-001）')
    expect(errorDisplay('NOT-A-CODE')).toBe(`系统繁忙，请稍后再试（${FALLBACK_ERROR_CODE}）`)
    expect(errorDisplay(undefined)).toBe(`系统繁忙，请稍后再试（${FALLBACK_ERROR_CODE}）`)
    expect(isKnownCode('TDCA-E-GOV-PERM-002')).toBe(true)
    expect(isKnownCode(42)).toBe(false)
  })
})

describe('客户端拒绝面显示「码＋中文短句」（段一验收）', () => {
  it('后端带 code → detail=显示串、rawDetail 留原文、code 透传', async () => {
    mockFetch.mockResolvedValue(
      jsonResponse(
        { detail: 'GRANT_REQUIRED: 无有效授权件', code: 'TDCA-E-AUTHZ-PERM-001' } as RawEnvelope,
        false,
        403,
      ),
    )
    const res = await api.get('/api/v1/cluster/execute')
    expect(res.ok).toBe(false)
    if (!res.ok) {
      expect(res.code).toBe('TDCA-E-AUTHZ-PERM-001')
      expect(res.detail).toBe('当前账户无权执行此操作（TDCA-E-AUTHZ-PERM-001）')
      expect(res.rawDetail).toBe('GRANT_REQUIRED: 无有效授权件')
    }
  })

  it('后端无 code（旧响应）→ 回落原 detail，不捏造码', async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ detail: '旧版裸文案' } as RawEnvelope, false, 400),
    )
    const res = await api.get('/api/v1/legacy')
    expect(res.ok).toBe(false)
    if (!res.ok) {
      expect(res.code).toBeUndefined()
      expect(res.detail).toBe('旧版裸文案')
    }
  })

  it('制度性拒绝码 GOV-PERM-002 显示制度短句', async () => {
    mockFetch.mockResolvedValue(
      jsonResponse(
        { detail: 'PUBLIC_SPACE_VIOLATION: 命中负空间', code: 'TDCA-E-GOV-PERM-002' } as RawEnvelope,
        false,
        400,
      ),
    )
    const res = await api.post('/api/v1/ownership/register', {})
    expect(res.ok).toBe(false)
    if (!res.ok) {
      expect(res.detail).toBe('本次操作被制度性拒绝（合规前置未过）（TDCA-E-GOV-PERM-002）')
    }
  })
})
