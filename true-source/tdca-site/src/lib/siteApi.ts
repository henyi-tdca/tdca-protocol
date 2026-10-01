// tdca-site 期 1 内部 API 助手
// 口令门：x-tdca-site-gate 由访问者输入一次，仅存 sessionStorage（不落文件、不进仓库）
const GATE_KEY = 'tdca_site_gate'
const WRITE_KEY = 'tdca_site_write'

export function getGate(): string {
  return sessionStorage.getItem(GATE_KEY) ?? ''
}

export function setGate(v: string): void {
  sessionStorage.setItem(GATE_KEY, v)
}

// 写令牌（B-4 写鉴权）：仅存 sessionStorage，不落任何文件/产物
export function getWriteToken(): string {
  return sessionStorage.getItem(WRITE_KEY) ?? ''
}

export function setWriteToken(v: string): void {
  if (v) sessionStorage.setItem(WRITE_KEY, v)
  else sessionStorage.removeItem(WRITE_KEY)
}

export class GateRequired extends Error {}

async function siteFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`/api/site${path}`, {
    ...init,
    headers: {
      ...(getGate() ? { 'x-tdca-site-gate': getGate() } : {}),
      ...(getWriteToken() ? { Authorization: `TDCA-CRT-${getWriteToken()}` } : {}),
      ...(init.headers || {}),
    },
  })
}

export async function siteGet<T>(path: string): Promise<T> {
  const res = await siteFetch(path)
  if (res.status === 401) throw new GateRequired()
  if (!res.ok) throw new Error(`API ${res.status}`)
  return (await res.json()) as T
}

export async function sitePost<T>(path: string, body: unknown, extraHeaders?: Record<string, string>): Promise<T> {
  const res = await siteFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(extraHeaders || {}) },
    body: JSON.stringify(body),
  })
  if (res.status === 401) throw new GateRequired()
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw Object.assign(new Error(`API ${res.status}`), { status: res.status, data })
  return data as T
}

export const FAMILIES: { key: string; label: string; desc: string }[] = [
  { key: 'whitepaper', label: '白皮书', desc: '治理与认知基础设施白皮书' },
  { key: 'paper', label: '论文', desc: '数学基础 / 函数白皮书 / 专著与实证证据' },
  { key: 'regulation', label: '公约条例', desc: '对外公约与条例文本' },
  { key: 'cop-library', label: 'COP 库', desc: '协议算子与场景编译件' },
]
