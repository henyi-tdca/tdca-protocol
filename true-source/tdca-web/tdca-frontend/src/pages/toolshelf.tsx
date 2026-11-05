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
// L1SI197 TOOLSHELF-001：A 档四包上卡（A-2/A-3/A-4/A-5，白名单制出包），
// 沿用本卡壳（S-3），卡内加行呈现 依赖／下载／sha256／许可 四小字段；
// 四卡均 status=dev（包已备、货架可见，下载／试算入口待部署后可用）。
// A-1/A-6 源缺口不做卡（回报 -089 具名停报）。
// L1SI197 MERGEUP-001：A-1 治理七件＋A-6 法务智能体两包上卡（回报 -094/-095 出包毕），
// 与四卡同式；A-1 卡 deps 显标「依赖 PyYAML，非零依赖」（令面硬要求）。
// L1SI197 MBUP-001：信箱协作（MAILBOX-COLLAB）独立产品线一卡（回报 -097 三包出包毕），
// ⛔ 与上列六卡混列——独立成区；卡内三分下载（spec／refimpl／bundle，⛔ 合成一 zip）；
// 卡面三标：零依赖（三包皆纯标准库，venv 无 PyYAML 实证）／协议附条件生效
// （条例 V1.0-FROZEN 乙案，灰度补录条件未竟前不视为完全生效）／半自动档（全自动 ⛔ 上线）。
// spec 条例四件之在册编号属已裁保留（核证单在册），其余件六模式复扫零命中。
// L1SI197 MANUPLOAD-001：六卡＋信箱卡各加「使用手册 V1.0-FROZEN」行（链 /official-assets）。
// ---------------------------------------------------------------------------
type ToolStatus = 'ok' | 'dev' | 'off'
type ToolNature = 'real' | 'simulated' | 'synthetic'
interface PublicTool {
  name: string
  use: string
  nature: ToolNature
  status: ToolStatus
  getLabel: string
  getHref: string
  date: string
  /** 卡壳 testid：缺省沿用 tool-card-<status>（兼容批3 B块断言），新卡各自独立 */
  tid?: string
  /** 以下四小字段为 A 档包卡加行呈现（令面六字段之余三项：依赖／下载／sha256／许可） */
  deps?: string
  pkg?: string
  sha256_16?: string
  sha256?: string
  license?: string
}
const PUBLIC_TOOLS: PublicTool[] = [
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
  {
    name: '微交付税收（tdca-microtax）',
    use: '智能体微交付实时计税与税款预缴托管：T(y_t) 分项税额 → 预缴 → 税后净额分配。',
    nature: 'simulated',
    status: 'dev',
    getLabel: '在线试算',
    getHref: '/microtax-calculator.html',
    date: '上卡 2026-11-05（待部署）',
    tid: 'tool-card-a2',
    deps: 'Python≥3.10 标准库＋同货架 tdca-nsfl-compiler（A-3）',
    pkg: 'tdca-microtax-A2-v1.0.zip（下载待部署）',
    sha256_16: 'f830375cc327bdbe',
    sha256: 'f830375cc327bdbea6af3c2968bb0a71c1f7b69d8cc7cb6a68c34555cb272f50',
    license: 'Apache-2.0',
  },
  {
    name: 'NSFL 编译器（tdca-nsfl-compiler）',
    use: '负空间约束语言编译器核心：词法／语法／语义＋⊗⊘⊙ 运算符＋schema 校验＋IR。',
    nature: 'real',
    status: 'dev',
    getLabel: '下载（待部署）',
    getHref: '',
    date: '上卡 2026-11-05（待部署）',
    tid: 'tool-card-a3',
    deps: 'Python≥3.10 标准库',
    pkg: 'tdca-nsfl-compiler-A3-v1.0.zip（下载待部署）',
    sha256_16: '333c8bcb12c026cc',
    sha256: '333c8bcb12c026cc169bd2e64bee1952a6c143a72a0382d6aa5328bda51200af',
    license: 'Apache-2.0',
  },
  {
    name: '证书工具（tdca-cert-tool）',
    use: 'TDCA L1 兼容性认证：MCP 连通／准入三态／存证哈希链／NSFL 熔断分级／可审计性。',
    nature: 'real',
    status: 'dev',
    getLabel: '下载（待部署）',
    getHref: '',
    date: '上卡 2026-11-05（待部署）',
    tid: 'tool-card-a4',
    deps: 'Python≥3.10 标准库',
    pkg: 'tdca-cert-tool-A4-v1.0.zip（下载待部署）',
    sha256_16: 'abb847f4cecab262',
    sha256: 'abb847f4cecab262693da4aac7d752a8648c7965a7f44e533b92f250bd48a610',
    license: 'Apache-2.0',
  },
  {
    name: '商业调用规则（tdca-call-rules）',
    use: '商业调用规则引擎：日抛判定／MOU 硬锚定／停机定理／税收计算与调用记录。',
    nature: 'simulated',
    status: 'dev',
    getLabel: '下载（待部署）',
    getHref: '',
    date: '上卡 2026-11-05（待部署）',
    tid: 'tool-card-a5',
    deps: 'Python≥3.10 标准库',
    pkg: 'tdca-call-rules-A5-v1.0.zip（下载待部署）',
    sha256_16: 'e8a80d05dc9d6456',
    sha256: 'e8a80d05dc9d6456fd43de3a125a8c228564baca4f109b2dd29b8f1ed06adb53',
    license: 'Apache-2.0',
  },
  {
    name: '治理工具集（tdca-govtools）',
    use: '治理侧七件单文件工具：链验／纪律核／信箱台账／日巡检／周深核／运维日报／交付封签。',
    nature: 'real',
    status: 'dev',
    getLabel: '下载（待部署）',
    getHref: '',
    date: '上卡 2026-11-05（待部署）',
    tid: 'tool-card-a1',
    deps: 'Python≥3.10 标准库＋PyYAML（依赖 PyYAML，非零依赖）',
    pkg: 'tdca-govtools-A1-v1.0.zip（下载待部署）',
    sha256_16: 'a1716bf9cd8a71c7',
    sha256: 'a1716bf9cd8a71c7ff542cf13f44cd7e100f08b560712ea34ea10b504b6542f2',
    license: 'Apache-2.0',
  },
  {
    name: '法务智能体（tdca-legal-agent）',
    use: '法学家工作的放大器与一致性校验器：批量初筛／交叉验证／NCA 铸造，不替代法学家。',
    nature: 'real',
    status: 'dev',
    getLabel: '下载（待部署）',
    getHref: '',
    date: '上卡 2026-11-05（待部署）',
    tid: 'tool-card-a6',
    deps: 'Python≥3.10 标准库（零依赖）',
    pkg: 'tdca-legal-agent-A6-v1.0.zip（下载待部署）',
    sha256_16: '5afc6a786257ed71',
    sha256: '5afc6a786257ed711ebb08a89922f2cb9eed3cc9852a4a8a61e76b4b4af9df3f',
    license: 'Apache-2.0',
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
              data-testid={t.tid ?? `tool-card-${t.status}`}
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
              {t.deps && (
                <dl className="mt-2 space-y-0.5 text-[11px] leading-relaxed text-gray-500">
                  <div><dt className="inline text-gray-400">依赖：</dt><dd className="inline">{t.deps}</dd></div>
                  <div><dt className="inline text-gray-400">下载：</dt><dd className="inline">{t.pkg}</dd></div>
                  <div><dt className="inline text-gray-400">sha256：</dt><dd className="inline" title={t.sha256}>{t.sha256_16}（前 16 位）</dd></div>
                  <div><dt className="inline text-gray-400">许可：</dt><dd className="inline">{t.license}</dd></div>
                  <div><dt className="inline text-gray-400">手册：</dt><dd className="inline"><Link to="/official-assets" className="text-blue-700 underline hover:bg-blue-50">使用手册 V1.0-FROZEN</Link></dd></div>
                </dl>
              )}
              <p className="mt-2 text-[11px] text-gray-400">{t.date}</p>
            </div>
          )
        })}
      </div>
      <p className="mt-2 text-[11px] text-gray-400">上架／下架由 operator 提交、创始人核；本区只做呈现与状态位。</p>
    </section>
  )
}

/** 信箱协作产品线（MAILBOX-COLLAB）三包：卡内三分下载，独立成区（MBUP-001） */
interface MailboxPkg {
  pkg: string
  bytes: number
  sha256_16: string
  sha256: string
  note: string
}
const MAILBOX_PKGS: MailboxPkg[] = [
  {
    pkg: 'tdca-mailbox-spec-v1.0.zip',
    bytes: 25662,
    sha256_16: '3E7677933BDD75A5',
    sha256: '3e7677933bdd75a5d35433d6576842617ecb90818078fc6edc842e3c8774d9a1',
    note: '协议条例 V1.0-FROZEN（人读版＋机读版）＋附件A（全部条款并入）＋五夹目录约定／回报首行七段／状态机图',
  },
  {
    pkg: 'tdca-mailbox-refimpl-v1.0.zip',
    bytes: 19630,
    sha256_16: 'B0FE22EB52FF2DBC',
    sha256: 'b0fe22eb52ff2dbcaa20f8dbfaf89daeae0d9077752a2dbf44ac7e6c93d0dea0',
    note: '参考实现五件（台账／扫描／归位／投放／断言集）＋JSON→YAML 发射器，默认信箱根取脚本同级 mailbox/，可 --mailbox-root 覆盖',
  },
  {
    pkg: 'tdca-mailbox-bundle-v1.0.zip',
    bytes: 7383,
    sha256_16: '834DA8BB322D6C50',
    sha256: '834da8bb322d6c50c00de3d55750f7e3ad82ffd1de6b62dadc19cde38441e865',
    note: '一键起盘（建五夹＋写样例＋自测＋打印态分布）＋脱敏样例台账 ledger.sample.json',
  },
]

/** 信箱协作独立卡区：⛔ 与公开货架六卡混列 */
function MailboxCollabSection() {
  return (
    <section data-testid="toolshelf-mailbox" aria-label="信箱协作产品线">
      <h2 className="mt-6 text-base font-semibold text-gray-900">信箱协作（MAILBOX-COLLAB）</h2>
      <div className="mt-2 grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
        <div data-testid="tool-card-mailbox" className="rounded-xl border border-indigo-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-gray-900">信箱协作协议与工具链（tdca-mailbox）</h3>
          <p className="mt-1 text-xs leading-relaxed text-gray-600">
            人机协作信箱协议（五夹目录／回报首行七段／件态状态机）＋纯标准库参考实现＋一键起盘；
            执行侧与智库之间件流 mailbox-collab 的产品化三包。
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px]">
            <span className="rounded bg-emerald-100 px-1.5 py-px font-medium text-emerald-700">零依赖（纯标准库）</span>
            <span className="rounded bg-amber-100 px-1.5 py-px font-medium text-amber-700">协议附条件生效</span>
            <span className="rounded bg-sky-100 px-1.5 py-px font-medium text-sky-700">半自动档</span>
            <span className="rounded bg-amber-600 px-1.5 py-px font-medium text-white">在建</span>
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-gray-500">
            附条件生效：条例 V1.0-FROZEN（乙案）须于灰度门补录条件成就后方完全生效，此前以在册条件为准；
            半自动档：全自动档 ⛔ 上线。三包皆经干净 venv（不装 PyYAML）四路冒烟实证零依赖。
          </p>
          <dl className="mt-2 space-y-1.5 text-[11px] leading-relaxed text-gray-500">
            {MAILBOX_PKGS.map((p) => (
              <div key={p.pkg} className="rounded-md border border-gray-100 p-1.5">
                <div>
                  <dt className="inline text-gray-400">下载：</dt>
                  <dd className="inline">
                    <a className="text-blue-700 underline hover:bg-blue-50" href={`/downloads/${p.pkg}`}>{p.pkg}</a>
                    （{p.bytes} B）
                  </dd>
                </div>
                <div><dt className="inline text-gray-400">sha256：</dt><dd className="inline" title={p.sha256}>{p.sha256_16}（前 16 位）</dd></div>
                <div><dt className="inline text-gray-400">许可：</dt><dd className="inline">Apache-2.0</dd></div>
                <div><dt className="inline text-gray-400">手册：</dt><dd className="inline"><Link to="/official-assets" className="text-blue-700 underline hover:bg-blue-50">使用手册 V1.0-FROZEN</Link></dd></div>
                <div><dt className="inline text-gray-400">含：</dt><dd className="inline">{p.note}</dd></div>
              </div>
            ))}
          </dl>
          <p className="mt-2 text-[11px] text-gray-400">上卡 2026-11-05；上架由 operator 提交、创始人核；本区只做呈现与状态位。</p>
        </div>
      </div>
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
      <MailboxCollabSection />
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
