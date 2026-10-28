// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: B5-NEWZONES-001 项四 · 运维「我的」（运维独立站点内新增）
// 约束矩阵: TDCA-DESIGN-OPS-ME-001（两套「我的」独立——用户「我的」管自己的事，
//   运维「我的」管站与服务的事；⛔ 不复用用户 /me 组件、⛔ 不共路由 S-6）
//   ＋ B5 交办令项四（六栏只读占位；申诉受理深度未定→只读；运维助手候裁→不设）
// 鉴权: 沿运维独立入口（tdca-ops realm ＋ 来源白名单，nginx 面）；本页为只读占位，零写动作
// =============================================================================
import { PageShell } from './PageShell'

interface OpsMeSection {
  key: string
  title: string
  items: string[]
  note: string
}

/** 六栏只读占位（照 DESIGN-OPS-ME-001 §三；申诉受理只读；⛔ 无运维助手） */
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
    items: ['私域服务可用性', '服务状态', '工单', '申诉受理（只读队列）'],
    note: '私域服务维护面：申诉受理与用户申诉端成对，本期为只读队列，可处置深度候裁。',
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

export function OpsMePage() {
  return (
    <PageShell dataNature="real"
      title="运维我的（站与服务的）"
      dataSource="静态占位（六栏只读；功能面随运维制度与在册功能项分批接通）"
      permission="登录 DID（运维身份；沿运维独立入口 tdca-ops 鉴权）"
      description="运维管理员的「我的」：管站与服务的事——站务／服务／治理操作／审计与留痕／应急／账户六栏。与用户「我的」（管自己的事）两套独立、内容不重叠。"
    >
      <div data-testid="ops-me-page" className="space-y-4">
        <p className="rounded-lg border border-gray-200 bg-gray-50/60 p-3 text-xs leading-relaxed text-gray-500">
          本期为六栏只读占位：只列栏目与口径，不含可执行操作。各栏功能面随运维制度与在册功能项分批接通；
          全程留痕（无存证不执行）。本页与用户「我的」零复用——路由不共、组件不共。
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          {SECTIONS.map((s) => (
            <section key={s.key} data-testid={s.key} className="rounded-lg border border-gray-200 bg-white p-3">
              <h3 className="mb-1.5 flex flex-wrap items-center gap-2 text-sm font-semibold text-gray-900">
                {s.title}
                {/* B3-GATE C块：未实现处一律标「建设中」＋「预计批次」（照 L1SI176-B3-GATE-001 §四③） */}
                <span data-testid={`${s.key}-building`} className="rounded border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-[10px] font-normal text-amber-700">建设中</span>
                <span className="text-[10px] font-normal text-gray-400">预计批次：未定（随运维制度件转正排期）</span>
              </h3>
              <ul className="space-y-1">
                {s.items.map((it) => (
                  <li key={it} className="text-xs text-gray-600">· {it}</li>
                ))}
              </ul>
              <p className="mt-2 text-[11px] text-gray-400">{s.note}</p>
            </section>
          ))}
        </div>
      </div>
    </PageShell>
  )
}
