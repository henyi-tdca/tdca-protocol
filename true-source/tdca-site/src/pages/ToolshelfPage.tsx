// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: P4 /toolshelf 工具货架（上站）
// 约束矩阵: 期一开工令 P4（站内工具/模板目录；配置类须过准入闸门）
// 复用: PageShell / SimulatedBadge / api（会话令牌自动注入）
// =============================================================================
import { useEffect, useState } from 'react'
import { api } from '@/lib/client'
import { PageShell } from '@/components/PageShell'
import { SimulatedBadge } from '@/lib/SimulatedBadge'

interface ToolView {
  tool_id: string
  name: string
  category: string
  description: string | null
  version: string | null
  requires_grant: boolean
  status: string
}

const CATEGORY_LABEL: Record<string, string> = {
  compiler: '编译器',
  adapter: '适配器',
  template: '模板',
  other: '其他',
}

export function ToolshelfPage() {
  const [rows, setRows] = useState<ToolView[]>([])
  const [msg, setMsg] = useState('')
  const [name, setName] = useState('')
  const [category, setCategory] = useState('compiler')
  const [requiresGrant, setRequiresGrant] = useState(false)
  const [tpl, setTpl] = useState<{
    version: string
    version_source: string
    effective_status: string
    effective_source: string
    authority: string
    files: { lang: string; filename: string; content: string; sha256_8: string }[]
  } | null>(null)
  const [tplMsg, setTplMsg] = useState('')

  const load = async () => {
    const r = await api.get<{ tools: ToolView[] }>('/api/v1/toolshelf/list')
    if (r.ok) setRows(r.data.tools)
  }
  useEffect(() => { void load() }, [])

  const onRegister = async () => {
    setMsg('')
    const r = await api.post<{ tool_id: string }>(
      '/api/v1/toolshelf/register',
      { name, category, requires_grant: requiresGrant })
    if (!r.ok) { setMsg(`上架失败：${r.reason}`); return }
    setMsg(`已上架：${r.data.tool_id}`)
    setName('')
    void load()
  }

  const onTemplate = async () => {
    setTplMsg('')
    const r = await api.get<{
      version: string
      version_source: string
      effective_status: string
      effective_source: string
      authority: string
      files: { lang: string; filename: string; content: string; sha256_8: string }[]
    }>('/api/v1/toolshelf/template/auth-contract')
    if (!r.ok) { setTplMsg(`模板加载失败：${r.reason}`); return }
    setTpl(r.data)
  }

  const download = (filename: string, content: string) => {
    const url = URL.createObjectURL(new Blob([content], { type: 'text/plain;charset=utf-8' }))
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <PageShell
      title="工具货架（P4）"
      dataSource="A-15 /api/v1/toolshelf/*（工具/模板目录）"
      permission="登录 DID（上架须 operator）"
      description="站内工具与模板目录：编译器、适配器等；配置类工具须凭授权件过准入闸门。">
      <section data-testid="toolshelf-list">
        <h2>货架</h2>
        <SimulatedBadge nature="simulated" />
        <ul>
          {rows.map((t) => (
            <li key={t.tool_id}>
              [{CATEGORY_LABEL[t.category] ?? t.category}] {t.name}
              {t.requires_grant ? '（配置类·须授权件）' : ''}
            </li>
          ))}
        </ul>
      </section>
      <section data-testid="toolshelf-register">
        <h2>工具上架</h2>
        <input placeholder="工具名" value={name} onChange={(e) => setName(e.target.value)} />
        <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="类目">
          <option value="compiler">编译器</option>
          <option value="adapter">适配器</option>
          <option value="template">模板</option>
          <option value="other">其他</option>
        </select>
        <label>
          <input type="checkbox" checked={requiresGrant}
            onChange={(e) => setRequiresGrant(e.target.checked)} />
          配置类（调用须过准入闸门）
        </label>
        <button onClick={onRegister}>上架</button>
        {msg && <p role="status">{msg}</p>}
      </section>
      <section data-testid="toolshelf-template">
        <h2>模板区 · 授权件模板</h2>
        <p>唯一权威源＝在仓《授权件模板》TDCA-TEMPLATE-AUTH-001（引用在仓、逐字一致；与所有者缔约授权书不可互替）。</p>
        <button onClick={onTemplate}>查看模板</button>
        {tplMsg && <p role="status">{tplMsg}</p>}
        {tpl && (
          <div>
            <p data-testid="tpl-version">件内版本：{tpl.version}（{tpl.version_source}）</p>
            <p data-testid="tpl-effective">生效：{tpl.effective_status}（{tpl.effective_source}）</p>
            <p>{tpl.authority}</p>
            <ul>
              {tpl.files.map((f) => (
                <li key={f.lang}>
                  [{f.lang}] {f.filename}（sha256_8：{f.sha256_8}）
                  <button onClick={() => download(f.filename, f.content)}>下载</button>
                  <details>
                    <summary>查看</summary>
                    <pre>{f.content}</pre>
                  </details>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>
    </PageShell>
  )
}
