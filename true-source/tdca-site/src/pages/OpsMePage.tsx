// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: ALPHA-C 项五 · 运维「我的」六栏接真实只读数据
// 约束矩阵: TDCA-DESIGN-OPS-ME-001（两套「我的」独立；⛔ 不复用用户 /me 组件、⛔ 不共路由 S-6）
//   ＋ ALPHA-C（L1SI214-ALPHA-ALL-001 C-5）：六栏只读接实显——站务/治理操作/审计与留痕/账户
//   四栏取真实只读端点；服务/应急无在册数据源 → 如实标「暂无数据」；⛔「建设中」禁语
// 鉴权: 沿运维独立入口（tdca-ops realm ＋ 来源白名单，nginx 面）；本页只读，零写动作
// 数据源: /api/v1/auth/me（账户）·/api/v1/announcements/list（站务）·/api/v1/toolshelf/list（治理操作）
//   ·/api/v1/me/nca（审计与留痕）；取不到即 fail-closed 标「暂无数据」，不猜测数据
// =============================================================================
import { useEffect, useState } from 'react'
import { PageShell } from '@/components/PageShell'
import { api } from '@/lib/client'

interface OpsMeSection {
  key: string
  title: string
  items: string[]
  note: string
}

/** 六栏（照 DESIGN-OPS-ME-001 §三；申诉受理只读；⛔ 无运维助手） */
const SECTIONS: OpsMeSection[] = [
  {
    key: 'ops-me-site',
    title: '站务',
    items: ['公域内容在位核对', '公开面守检', '入口与白名单核对', '公告发布（内容须明示）'],
    note: '公域维护核对面：照运维制度纪律在位核对，留痕全程落存证。',
  },
  {
    key: 'ops-me-service',
    title: '服务',
    items: ['私域服务可用性', '服务状态', '工单', '申诉受理（受理通道在建，当前仅登记不处置）'],
    note: '私域服务维护面：申诉受理与用户申诉端同口径——受理通道在建，当前仅登记不处置，可处置深度候裁。',
  },
  {
    key: 'ops-me-governance',
    title: '治理操作',
    items: ['评审队列', '形式化入站', '工具上架', '集群准入'],
    note: '治理操作面：与站点运维端既有功能项衔接，操作入口照在册各面。',
  },
  {
    key: 'ops-me-audit',
    title: '审计与留痕',
    items: ['存证台账', '留痕复核', '倒查'],
    note: '审计面：每一次操作皆留存证（无存证不执行），台账与倒查照在册口径。',
  },
  {
    key: 'ops-me-emergency',
    title: '应急',
    items: ['回退点', '熔断状态', '安全事件登记与闭合'],
    note: '应急面：回退与熔断状态核对，事件登记到闭合全程留痕。',
  },
  {
    key: 'ops-me-account',
    title: '账户',
    items: ['会话', '密码'],
    note: '运维本人之账户：与用户面同构但独立，互不混用。',
  },
]

/** 实显数据（null＝未取到，如实标暂无数据；不猜测、不默认） */
interface OpsMeData {
  site: number | null
  governance: number | null
  audit: number | null
  account: { role: string; expiresInMin: number } | null
}

/** 每栏实显一行（照端点真值；取不到给暂无数据说明） */
const FACT_TEXT: Record<string, (d: OpsMeData) => string> = {
  'ops-me-site': (d) =>
    d.site === null ? '暂无数据（公告列表未取到，不猜测）' : `公告在架 ${d.site} 条（公告栏公开列表实显）`,
  'ops-me-service': () => '暂无数据（服务面无在册数据源，如实标注）',
  'ops-me-governance': (d) =>
    d.governance === null ? '暂无数据（工具货架未取到，不猜测）' : `工具在架 ${d.governance} 件（工具货架实显）`,
  'ops-me-audit': (d) =>
    d.audit === null ? '暂无数据（本人存证明细未取到，不猜测）' : `本人存证留痕 ${d.audit} 条（NCA 明细实显）`,
  'ops-me-emergency': () => '暂无数据（应急面无在册数据源，如实标注）',
  'ops-me-account': (d) =>
    d.account === null
      ? '暂无数据（会话状态未取到，登录后可见）'
      : `当前身份 ${d.account.role} · 会话剩余约 ${d.account.expiresInMin} 分钟（会话状态实显）`,
}

const HAS_DATA: Record<string, (d: OpsMeData) => boolean> = {
  'ops-me-site': (d) => d.site !== null,
  'ops-me-service': () => false,
  'ops-me-governance': (d) => d.governance !== null,
  'ops-me-audit': (d) => d.audit !== null,
  'ops-me-emergency': () => false,
  'ops-me-account': (d) => d.account !== null,
}

export function OpsMePage() {
  const [data, setData] = useState<OpsMeData>({ site: null, governance: null, audit: null, account: null })

  useEffect(() => {
    let alive = true
    void (async () => {
      const [ann, tools, nca, me] = await Promise.all([
        api.get<{ count: number }>('/api/v1/announcements/list'),
        api.get<{ count: number }>('/api/v1/toolshelf/list'),
        api.get<{ total: number }>('/api/v1/me/nca?page=1&limit=1'),
        api.get<{ role: string; expires_in_s: number }>('/api/v1/auth/me'),
      ])
      if (!alive) return
      setData({
        site: ann.ok ? (ann.data.count ?? null) : null,
        governance: tools.ok ? (tools.data.count ?? null) : null,
        audit: nca.ok ? (nca.data.total ?? null) : null,
        account: me.ok && me.data.role
          ? { role: me.data.role, expiresInMin: Math.max(0, Math.round((me.data.expires_in_s ?? 0) / 60)) }
          : null,
      })
    })()
    return () => {
      alive = false
    }
  }, [])

  return (
    <PageShell
      title="运维我的（站与服务的）"
      dataSource="实显四栏只读：/api/v1/auth/me（账户）·/api/v1/announcements/list（站务）·/api/v1/toolshelf/list（治理操作）·/api/v1/me/nca（审计与留痕）；服务／应急暂无数据"
      permission="登录 DID（运维身份；沿运维独立入口 tdca-ops 鉴权）"
      description="运维管理员的「我的」：管站与服务的事——站务／服务／治理操作／审计与留痕／应急／账户六栏。与用户「我的」（管自己的事）两套独立、内容不重叠。"
    >
      <div data-testid="ops-me-page" className="space-y-4">
        <p className="rounded-lg border border-gray-200 bg-gray-50/60 p-3 text-xs leading-relaxed text-gray-500">
          六栏只读：站务／治理操作／审计与留痕／账户四栏接实显只读数据（接口取不到时如实标「暂无数据」，不猜测）；
          服务／应急暂无在册数据源，如实标注。不含可执行操作；全程留痕（无存证不执行）。
          本页与用户「我的」零复用——路由不共、组件不共。
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          {SECTIONS.map((s) => {
            const live = HAS_DATA[s.key](data)
            return (
              <section key={s.key} data-testid={s.key} className="rounded-lg border border-gray-200 bg-white p-3">
                <h3 className="mb-1.5 flex flex-wrap items-center gap-2 text-sm font-semibold text-gray-900">
                  {s.title}
                  {/* ALPHA-C：徽章改实显状态——有真值绿标「实显」，无真值灰标「暂无数据」 */}
                  <span
                    data-testid={`${s.key}-building`}
                    className={
                      live
                        ? 'rounded border border-green-200 bg-green-50 px-1.5 py-0.5 text-[10px] font-normal text-green-700'
                        : 'rounded border border-gray-200 bg-gray-50 px-1.5 py-0.5 text-[10px] font-normal text-gray-400'
                    }
                  >
                    {live ? '实显' : '暂无数据'}
                  </span>
                </h3>
                <p data-testid={`${s.key}-fact`} className="mb-1.5 text-xs text-gray-700">
                  · {FACT_TEXT[s.key](data)}
                </p>
                <ul className="space-y-1">
                  {s.items.map((it) => (
                    <li key={it} className="text-xs text-gray-600">· {it}</li>
                  ))}
                </ul>
                <p className="mt-2 text-[11px] text-gray-400">{s.note}</p>
              </section>
            )
          })}
        </div>
      </div>
    </PageShell>
  )
}
