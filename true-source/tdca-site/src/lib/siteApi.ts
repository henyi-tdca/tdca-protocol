// tdca-site 期 1 内部 API 助手
// 口令门：x-tdca-site-gate 由访问者输入一次，仅存 sessionStorage（不落文件、不进仓库）
const GATE_KEY = 'tdca_site_gate'

export function getGate(): string {
  return sessionStorage.getItem(GATE_KEY) ?? ''
}

export function setGate(v: string): void {
  sessionStorage.setItem(GATE_KEY, v)
}

export class GateRequired extends Error {}

export async function siteGet<T>(path: string): Promise<T> {
  const res = await fetch(`/api/site${path}`, {
    headers: getGate() ? { 'x-tdca-site-gate': getGate() } : {},
  })
  if (res.status === 401) throw new GateRequired()
  if (!res.ok) throw new Error(`API ${res.status}`)
  return (await res.json()) as T
}

export const FAMILIES: { key: string; label: string; desc: string }[] = [
  { key: 'whitepaper', label: '白皮书', desc: '治理与认知基础设施白皮书' },
  { key: 'paper', label: '论文', desc: '数学基础 / 函数白皮书 / 专著与实证证据' },
  { key: 'regulation', label: '公约条例', desc: '对外公约与条例文本' },
  { key: 'cop-library', label: 'COP 库', desc: '协议算子与场景编译件' },
]
