// tdca-site 期 1 内部 API 助手
// ACCESS-FIX-001-AMEND-1 交付一：页面口令门已撤（不再发 x-tdca-site-gate；公开面无口令提示）
const WRITE_KEY = 'tdca_site_write'

// 写令牌（B-4 写鉴权）：仅存 sessionStorage，不落任何文件/产物
export function getWriteToken(): string {
  return sessionStorage.getItem(WRITE_KEY) ?? ''
}

export function setWriteToken(v: string): void {
  if (v) sessionStorage.setItem(WRITE_KEY, v)
  else sessionStorage.removeItem(WRITE_KEY)
}

async function siteFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`/api/site${path}`, {
    ...init,
    headers: {
      ...(getWriteToken() ? { Authorization: `TDCA-CRT-${getWriteToken()}`, 'X-TDCA-Token-Type': 'execution' } : {}),
      ...(init.headers || {}),
    },
  })
}

export async function siteGet<T>(path: string): Promise<T> {
  const res = await siteFetch(path)
  if (!res.ok) throw new Error(`API ${res.status}`)
  return (await res.json()) as T
}

export async function sitePost<T>(path: string, body: unknown, extraHeaders?: Record<string, string>): Promise<T> {
  const res = await siteFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(extraHeaders || {}) },
    body: JSON.stringify(body),
  })
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
