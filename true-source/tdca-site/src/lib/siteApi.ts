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
  { key: 'regulation', label: '制度', desc: '制度／条例／规则／办法／章程／指引' },
  { key: 'help', label: '帮助', desc: '说明／示例／帮助' },
]
