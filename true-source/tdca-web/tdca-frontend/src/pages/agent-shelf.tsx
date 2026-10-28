// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 智能体区（组二 10 件以智能体形态呈现）
// 约束矩阵: 创始人 2026-10-04 明示「组二 10 件怎么呈现——智能体」
// 口径: 本区只办【呈现】——⛔ 不等于注册（注册触及注册登记制度与双轨身份，
//       另须明示、另走流程）；每条只列 名称／一句用途／形态；准入与否按在册流程。
// =============================================================================
import { PageShell } from './PageShell'

interface AgentEntry {
  name: string
  purpose: string
  form: string
}

const AGENT_GROUP2: AgentEntry[] = [
  { name: '认知对齐评测', purpose: '评测智能体输出与人类意图的对齐程度', form: '智能体' },
  { name: '配置权计量', purpose: '计量配置权调用与流转', form: '智能体' },
  { name: '场景沙盒', purpose: '场景配置隔离验证', form: '智能体' },
  { name: '存证审计', purpose: '存证链核验与审计', form: '智能体' },
  { name: '商户闭环', purpose: '商户接入到结算的闭环流程', form: '智能体' },
  { name: '协作编排', purpose: '多智能体协作流程编排', form: '智能体' },
  { name: '编码智能体', purpose: '代码生成与工程协作', form: '智能体' },
  { name: '物联计量网关', purpose: '物联侧计量数据采集与上报', form: '智能体' },
  { name: '效用价值评估', purpose: '效用与价值水平评估计量', form: '智能体' },
  { name: '增值服务打包', purpose: '增值服务组合与打包', form: '智能体' },
]

/** 智能体区：组二 10 件呈现（呈现 ≠ 注册；准入与否按在册配置类准入流程另办） */
export function AgentShelfPage() {
  return (
    <PageShell dataNature="real"
      title="智能体区（组二 10 件呈现）"
      dataSource="静态呈现（呈现面；非注册数据）"
      permission="登录 DID"
      description="组二 10 件以智能体形态呈现：每条只列名称／一句用途／形态。"
    >
      <div className="space-y-4">
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"
           data-testid="agent-shelf-disclaimer">
          本区为呈现态：以上条目仅作站点呈现，未注册、未准入。
          智能体注册触及注册登记制度与双轨身份，须另行明示、另走流程；
          是否准入、以何种形态（演示／受限／正式）运行，按在册配置类准入流程办理。
        </p>
        <section data-testid="agent-shelf-list">
          <ul className="space-y-2">
            {AGENT_GROUP2.map((a) => (
              <li key={a.name}
                  className="rounded-lg border border-gray-200 bg-white p-3 text-sm">
                <span className="font-semibold text-gray-900">{a.name}</span>
                <span className="ml-2 text-gray-500">{a.purpose}</span>
                <span className="ml-2 rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                  形态：{a.form}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </PageShell>
  )
}
