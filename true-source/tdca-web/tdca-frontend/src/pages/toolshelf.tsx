// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: P4 /toolshelf 工具货架（上站）
// 约束矩阵: 期一开工令 P4（站内工具/模板目录；配置类须过准入闸门）
// 复用: PageShell / SimulatedBadge / api（会话令牌自动注入）
// =============================================================================
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api } from '@/api/client'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

// ---------------------------------------------------------------------------
// L1SI177 批3 B块：公开货架呈现（照已过点样三卡三态；条目卡五项：
// 名称／用途一句／数据性质／获取方式／状态徽标＋日期。只做呈现与状态位，
// ⛔ 不做自助上架后台——上架由 operator 提交、创始人核）
// ---------------------------------------------------------------------------
type ToolStatus = 'ok' | 'dev' | 'off'
type ToolNature = 'real' | 'simulated' | 'synthetic'
const PUBLIC_TOOLS: { name: string; use: string; nature: ToolNature; status: ToolStatus; getLabel: string; getHref: string; date: string }[] = [
  {
    name: '自助验链',
    use: '输入件名与哈希，自助核验公开件在册状态与链上留痕。',
    nature: 'real',
    status: 'ok',
    getLabel: '打开工具',
    getHref: '/verify',
    date: '更新 2026-10-28',
  },
  {
    name: '全站检索',
    use: '四族＋术语＋栏目页的一框检索；静态索引先行，结果带数据性质。',
    nature: 'simulated',
    status: 'dev',
    getLabel: '上线后可用',
    getHref: '',
    date: '更新 2026-10-27',
  },
  {
    name: '旧版演示脚本',
    use: '批 2.6 演示区旧脚本，已由新演示页替代，停止提供。',
    nature: 'synthetic',
    status: 'off',
    getLabel: '暂不可用',
    getHref: '',
    date: '下架 2026-10-20',
  },
]
const TOOL_STATUS: Record<ToolStatus, { label: string; badge: string }> = {
  ok: { label: '可用', badge: 'bg-emerald-600 text-white' },
  dev: { label: '在建', badge: 'bg-amber-600 text-white' },
  off: { label: '下架', badge: 'bg-gray-400 text-white' },
}
const TOOL_NATURE: Record<ToolNature, { label: string; badge: string }> = {
  real: { label: '真实', badge: 'bg-emerald-100 text-emerald-700' },
  simulated: { label: '模拟', badge: 'bg-amber-100 text-amber-700' },
  synthetic: { label: '合成', badge: 'bg-slate-200 text-slate-600' },
}

/** 公开货架三卡（点样形态；窄屏自动单列，卡内不折行霸屏） */
function PublicToolCards() {
  return (
    <section data-testid="toolshelf-cards" aria-label="公开货架">
      <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
        {PUBLIC_TOOLS.map((t) => {
          const st = TOOL_STATUS[t.status]
          const na = TOOL_NATURE[t.nature]
          return (
            <div
              key={t.name}
              data-testid={`tool-card-${t.status}`}
              className={`rounded-xl border border-gray-200 bg-white p-4 ${t.status === 'off' ? 'opacity-60' : ''}`}
            >
              <h3 className="text-sm font-semibold text-gray-900">{t.name}</h3>
              <p className="mt-1 min-h-[34px] text-xs leading-relaxed text-gray-600">{t.use}</p>
              <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px]">
                <span className={`rounded px-1.5 py-px font-medium ${na.badge}`}>{na.label}</span>
                <span className={`rounded px-1.5 py-px font-medium ${st.badge}`}>{st.label}</span>
              </div>
              <div className="mt-2 text-xs">
                {t.getHref ? (
                  <Link to={t.getHref} className="rounded-md border border-blue-700 px-2.5 py-0.5 text-blue-700 hover:bg-blue-50">
                    {t.getLabel}
                  </Link>
                ) : (
                  <span className="text-gray-400">{t.getLabel}</span>
                )}
              </div>
              <p className="mt-2 text-[11px] text-gray-400">{t.date}</p>
            </div>
          )
        })}
      </div>
      <p className="mt-2 text-[11px] text-gray-400">上架／下架由 operator 提交、创始人核；本区只做呈现与状态位。</p>
    </section>
  )
}

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
      <PublicToolCards />
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
