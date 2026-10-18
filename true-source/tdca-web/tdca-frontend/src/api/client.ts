// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F0-3 统一 API 客户端（三级接口 + NCA 水印 + fail-closed + WS + HUF token）
// 约束矩阵: TDCA-TASK-FRONTEND-001（FROZEN）§三 F0-3 + TDCA-FRONTEND-FRAMEWORK-001 §五
// 制度锚点: ID91（NCA 水印校验）/ ID92（模拟态标注）/ ID85（fail-closed）/ ID71（快慢分工）/ F-4+HUF（写操作 token）
// 先验分布: tdca-gateway:8100（/api/v1/* A 类 + /ws/events B-5 四通道 + B-4 鉴权中间件，29 测试绿）
// 配置权边界: L2 前端层；仅消费后端，不修改 FROZEN 库
// 预期分配: get/post/ws 三级接口 + 水印缺失拒绝 + fail-closed 降级 + HUF 写操作 token 注入
// 审计轨迹: TDCA-NCA-FRONTEND-F0-001
// 开发者: Reasonix（M）| 负空间版本: NSFL-V0.2 | MOU 锚定: 复用既有 gateway 契约
// =============================================================================

// L1SI153 段一：错误码表与显示串（一处常量，码与短句不分两处维护）
import { errorDisplay } from './errors'

export const BASE = import.meta.env.VITE_API_BASE ?? '' // M4 一体部署默认同源；开发态经 .env.development 指向 8100

export const WS_CHANNELS = ['handshake', 'tax_mou', 'notifier', 'audit'] as const
export type WsChannel = (typeof WS_CHANNELS)[number]

export type DataNature = 'real' | 'simulated'

/** NCA 水印校验结果：缺失或哈希不符 → 拒绝渲染（ID91） */
export type WatermarkVerdict = 'ok' | 'missing'

export interface ApiSuccess<T> {
  ok: true
  data: T
  watermark: string
  nature: DataNature
}
export interface ApiFailure {
  ok: false
  reason: 'watermark_missing' | 'fail_closed' | 'http_error' | 'unauthorized' | 'forbidden'
  status?: number
  detail?: string
  /** L1SI153 段一：后端错误码（TDCA-E-*）；缺失为 undefined */
  code?: string
  /** 后端原始文案（未被显示串改写前的 detail，备查/日志） */
  rawDetail?: string
}
export type ApiResult<T> = ApiSuccess<T> | ApiFailure

export interface RawEnvelope {
  nca_watermark?: string
  data_nature?: DataNature
  data?: unknown
  [k: string]: unknown
}

/** HUF 写操作 token（B-4：Authorization 完整值 = TDCA-CRT-{token}）；默认与 gateway 模拟态一致 */
export function hufToken(): string {
  return localStorage.getItem('tdca_huf_token') ?? import.meta.env.VITE_HUF_TOKEN ?? 'TDCA-CRT-demo-2026'
}

export function setHufToken(token: string): void {
  localStorage.setItem('tdca_huf_token', token)
}

// ---------------------------------------------------------------------------
// M3 会话接缝（F-2）：TDCA-SES 会话令牌 + 401/403 拦截 + 草稿兜底
// ---------------------------------------------------------------------------
const SESSION_KEY = 'tdca_session_token'
const EXPIRED_KEY = 'tdca:session:expired'

/** 会话过期/被踢事件（app-shell 监听 → 明确提示，不自动跳转，页面表单状态原样保留） */
export const SESSION_EXPIRED_EVENT = 'tdca:session-expired'

/** 匿名 401/403 事件（app-shell 监听 → 「内容需登录后可见」引导条，不静默） */
export const AUTH_REQUIRED_EVENT = 'tdca:auth-required'

export function sessionToken(): string | null {
  return sessionStorage.getItem(SESSION_KEY)
}
export function setSessionToken(token: string): void {
  sessionStorage.setItem(SESSION_KEY, token)
}
export function clearSessionToken(): void {
  sessionStorage.removeItem(SESSION_KEY)
}

/** 身份令牌（凭证四分面呈现用：账户管理面；现状待建，键位与 tdca-site 一致） */
const IDENTITY_KEY = 'tdca_identity_token'
export function identityToken(): string | null {
  return localStorage.getItem(IDENTITY_KEY)
}

/** 授权码（凭证四分面呈现用：资产使用面；现状待建，键位与 tdca-site 一致） */
const AUTHCODE_KEY = 'tdca_auth_code'
export function authCode(): string | null {
  return sessionStorage.getItem(AUTHCODE_KEY)
}

/** 草稿兜底（裁定③：被踢时数据不能丢）——表单页提交前 saveDraft，挂载时 loadDraft 回填 */
export function saveDraft(route: string, data: unknown): void {
  sessionStorage.setItem(`tdca:draft:${route}`, JSON.stringify(data))
}
export function loadDraft<T>(route: string): T | null {
  const raw = sessionStorage.getItem(`tdca:draft:${route}`)
  if (!raw) return null
  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}
export function clearDraft(route: string): void {
  sessionStorage.removeItem(`tdca:draft:${route}`)
}

/** 会话失效处理：清令牌 + 标记 + 广播事件（仅在持有会话时被拒才触发，登录失败不误触） */
function handleSessionRejected(ses: string | null): void {
  if (!ses) return
  clearSessionToken()
  sessionStorage.setItem(EXPIRED_KEY, JSON.stringify({ from: window.location.pathname, ts: Date.now() }))
  window.dispatchEvent(
    new CustomEvent(SESSION_EXPIRED_EVENT, { detail: { from: window.location.pathname } }),
  )
}

function wsBase(): string {
  return BASE.replace(/^http/, 'ws')
}

/** 响应 NCA 水印校验（ID91）：缺失即拒绝渲染 */
export function verifyWatermark(raw: RawEnvelope): WatermarkVerdict {
  return raw && typeof raw.nca_watermark === 'string' && raw.nca_watermark.length > 0 ? 'ok' : 'missing'
}

// ---------------------------------------------------------------------------
// 私有 HTTP 原语（既有契约方法复用；不附加水印语义，抛错语义保持）
// ---------------------------------------------------------------------------
async function httpGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`)
  return res.json() as Promise<T>
}

async function httpPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`)
  return res.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// F0-3 统一 API 客户端：三级接口 + NCA 水印 + fail-closed + WS + HUF token
// ---------------------------------------------------------------------------
export interface GetOptions {
  /** 水印缺失时是否仍返回降级（默认 false → 直接判 watermark_missing 拒绝） */
  tolerateMissingWatermark?: boolean
}

export interface PostOptions extends GetOptions {
  /** HUF 写操作：注入 Authorization: TDCA-CRT-{token}（B-4） */
  needHuf?: boolean
}

async function request<T>(
  method: 'GET' | 'POST',
  path: string,
  body: unknown,
  opts: PostOptions = {},
): Promise<ApiResult<T>> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const ses = sessionToken() // M3：会话令牌优先；无会话且 HUF 写操作 → B-4 静态令牌兜底
  if (ses) headers.Authorization = ses
  else if (opts.needHuf) headers.Authorization = hufToken()
  try {
    const res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: method === 'POST' ? JSON.stringify(body ?? {}) : undefined,
    })
    if (!res.ok) {
      if (res.status === 401 || res.status === 403) {
        if (ses) {
          handleSessionRejected(ses) // M3 会话失效拦截
        } else {
          // 匿名被拒：广播登录引导事件（app-shell 出提示条），不静默空页
          window.dispatchEvent(new CustomEvent(AUTH_REQUIRED_EVENT))
        }
      }
      // fail-closed：不猜测、不默认；401/403 给明确 reason 供页面内联提示
      // E-1（UX-PLAIN-001 批2）：解析后端错误原文（FastAPI detail），reason 保持兼容
      // L1SI153 段一：解析后端 code → 显示「码＋中文短句」（errors.ts 一处常量）；
      // 原始文案保留在 rawDetail，detail 为用户所见显示串
      let backendDetail: string | undefined
      let backendCode: string | undefined
      try {
        const errBody = (await res.json()) as { detail?: unknown; code?: unknown }
        if (typeof errBody?.detail === 'string') backendDetail = errBody.detail
        if (typeof errBody?.code === 'string') backendCode = errBody.code
      } catch { /* 非 JSON 错误体：detail 保持 undefined，回落 reason */ }
      const reason = res.status === 401 ? 'unauthorized' : res.status === 403 ? 'forbidden' : 'http_error'
      return {
        ok: false, reason, status: res.status,
        detail: backendCode ? errorDisplay(backendCode) : backendDetail,
        code: backendCode,
        rawDetail: backendDetail,
      }
    }
    const raw = (await res.json()) as RawEnvelope
    const verdict = verifyWatermark(raw)
    if (verdict !== 'ok' && !opts.tolerateMissingWatermark) {
      return { ok: false, reason: 'watermark_missing', detail: 'NCA 水印缺失，拒绝渲染' }
    }
    const nature: DataNature = raw.data_nature === 'real' ? 'real' : 'simulated' // ID92：非 real 一律模拟标注
    const data = (raw.data ?? raw) as T
    return { ok: true, data, watermark: raw.nca_watermark ?? '', nature }
  } catch (err) {
    // fail-closed：后端不可用 → 静态降级提示（不猜测数据）
    return { ok: false, reason: 'fail_closed', detail: err instanceof Error ? err.message : String(err) }
  }
}

/** WS 四通道订阅（B-5 /ws/events?channel={channel}）；返回取消订阅函数 */
export function wsSubscribe(
  channel: WsChannel,
  handlers: { onMessage: (msg: unknown) => void; onStatus?: (s: 'open' | 'close' | 'error') => void },
): () => void {
  const url = `${wsBase()}/ws/events?channel=${channel}`
  const socket = new WebSocket(url)
  socket.onopen = () => handlers.onStatus?.('open')
  socket.onclose = () => handlers.onStatus?.('close')
  socket.onerror = () => handlers.onStatus?.('error')
  socket.onmessage = (ev) => {
    try {
      handlers.onMessage(JSON.parse(ev.data as string))
    } catch {
      handlers.onMessage(ev.data)
    }
  }
  return () => socket.close()
}

// ---------------------------------------------------------------------------
// api 命名空间：既有契约方法（W7，保持签名）+ F0-3 三级接口
// ---------------------------------------------------------------------------
export interface SceneRuleIn {
  rule_id?: string
  ns_type: string
  operator: string
  parameter?: string | null
  unit?: string | null
}

export interface SceneIn {
  scene_id?: string
  rules: SceneRuleIn[]
}

export interface PreflightRequest {
  caller_scene: SceneIn
  callee_scene: SceneIn
  caller_tier?: string
  cross_scene_flag?: boolean
}

export interface HandshakeSummary {
  handshake_id: string
  status: string
  current_step: string | null
  preflight_status: string | null
  risk_premium: number
  escrow_id: string | null
  work_order_id: string | null
  nca_count: number
  human_gates: { gate1: boolean; gate2: boolean }
}

export const api = {
  // ---- F0-3 三级接口（水印/fail-closed/WS/HUF）----
  get: <T>(path: string, opts: GetOptions = {}) => request<T>('GET', path, null, opts),
  post: <T>(path: string, body: unknown, opts: PostOptions = {}) => request<T>('POST', path, body, opts),
  ws: wsSubscribe,
  verifyWatermark,
  hufToken,
  setHufToken,

  // ---- 既有契约方法（W7，只读，签名保持）----
  preflight: (callerScene: SceneIn, calleeScene: SceneIn, opts?: { caller_tier?: string; cross_scene_flag?: boolean }) =>
    httpPost<Record<string, unknown>>('/nsfl/preflight/check', {
      caller_scene: callerScene,
      callee_scene: calleeScene,
      caller_tier: opts?.caller_tier ?? 'L2',
      cross_scene_flag: opts?.cross_scene_flag ?? true,
    }).catch(() => null),
  handshakeStatus: (handshakeId: string) => httpGet<Record<string, unknown>>(`/handshake/status/${handshakeId}`),
  handshakeList: (page = 1, limit = 20, statusFilter?: string) => {
    const q = new URLSearchParams({ page: String(page), limit: String(limit) })
    if (statusFilter) q.set('status_filter', statusFilter)
    return httpGet<{ total: number; items: HandshakeSummary[] }>(`/handshake/list?${q}`)
  },
  handshakeDetail: (handshakeId: string) => httpGet<Record<string, unknown>>(`/handshake/detail?handshake_id=${handshakeId}`),
  ncaChain: (handshakeId: string) =>
    httpGet<{ chain: { index: number; nca_ref: string; link: string }[]; total: number }>(
      `/nca/chain?handshake_id=${handshakeId}`,
    ),
  workflowStatus: (workOrderId: string) =>
    httpGet<Record<string, unknown>>(`/workflow/status?execution_id=${workOrderId}`),
}
