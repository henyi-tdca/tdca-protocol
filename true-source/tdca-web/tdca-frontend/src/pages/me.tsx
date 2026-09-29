// =============================================================================
// TDCA 制度水印
// FC-ID: KIMI-WEB-DB-TASK-001-M5 | 目标函数: /me 个人后台（人类用户一屏聚合）
// 约束矩阵: M5-PLAN §三.1（六区块）+ 裁定②（只见自己名下）+ ID92（simulated 标注）
// 预期分配: MePage（会话卡 + 签批待办红签置顶 + 我的智能体 + 我批过的 + 沙盒 + 治理）
// =============================================================================
import { Link } from 'react-router'
import { useApiGet } from '@/shared/useApi'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

interface MeData {
  session: { username: string; role: string; expires_at: string; last_register_nca_id?: string | null }
  pending_count: number
  my_agents: { agent_id: string; name: string; five_role: string | null; status: string; attestation_state: string; audit_count: number; data_provenance: string }[]
  my_pending_sign: { request_id: string; agent_id: string; request_type: string; urgency: string | null; reason: string | null; ts: string }[]
  my_decided: { request_id: string; agent_id: string; status: string; ts: string }[]
  my_sandbox: { apply_id: string; result: string | null; ts: string }[]
  my_governance: { op: string; fuse_state: string | null; ts: string }[]
  note: string
}

const ROLE_LABEL: Record<string, string> = { founder: '创始人', operator: '运营者', viewer: '访客' }
const RESULT_LABEL: Record<string, string> = { admitted: '✅ 已入盒', denied: '❌ 未通过', pending: '⏳ 待审' }

/** M5 个人后台：谁的数据谁可见（须登录；未登录自动引导） */
export function MePage() {
  const { status, data } = useApiGet<MeData>('/api/v1/me/dashboard')

  return (
    <PageShell
      title="个人后台（我的）"
      dataSource="M5 GET /api/v1/me/dashboard（六区块一次聚合）"
      permission="须登录（M3 会话，谁的数据谁可见）"
      description="你的智能体、待你签批的请求、你批过的记录、你的沙盒申请与治理操作，一屏看全。"
    >
      {status === 'loading' && <p className="text-sm text-gray-400">加载中…</p>}
      {status === 'fail' && (
        <div data-testid="me-login-required" className="max-w-md rounded border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          这里是你自己的后台，需要先登录才能看。
          <Link to="/auth" className="ml-2 font-medium text-emerald-700 underline">去登录 →</Link>
        </div>
      )}
      {status === 'ok' && data && (
        <div className="space-y-5">
          {/* 会话卡 + 红签待办 */}
          <section className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div data-testid="me-session" className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="text-xs text-gray-500">当前登录</div>
              <div className="mt-1 text-lg font-semibold text-gray-800">
                {data.session.username}
                <span className="ml-2 rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{ROLE_LABEL[data.session.role] ?? data.session.role}</span>
              </div>
              <div className="mt-1 text-xs text-gray-400">会话有效至 {data.session.expires_at.slice(0, 19).replace('T', ' ')}</div>
              {data.session.last_register_nca_id && (
                <div data-testid="me-register-nca" className="mt-1 text-xs text-gray-400">
                  最近缔约存证 <span className="font-mono text-gray-500">{data.session.last_register_nca_id}</span>
                  （注册即缔约已落 NCA 链，可经审计透明页自查在链）
                </div>
              )}
            </div>
            <div data-testid="me-pending-card" className={`rounded-lg border p-4 ${data.pending_count > 0 ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-white'}`}>
              <div className="text-xs text-gray-500">待我签批</div>
              <div className={`mt-1 text-2xl font-bold ${data.pending_count > 0 ? 'text-red-700' : 'text-gray-700'}`}>{data.pending_count} 件</div>
              {data.pending_count > 0 && <Link to="/attestation/dynamic" className="text-xs font-medium text-red-700 underline">去签批 →</Link>}
            </div>
          </section>

          {/* 我的智能体 */}
          <section data-testid="me-agents" className="rounded-lg border border-gray-200 p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">我的智能体（{data.my_agents.length}）</h3>
            {data.my_agents.length === 0 && <p className="text-sm text-gray-400">名下暂无智能体——去 <Link to="/studio" className="text-emerald-700 underline">Agent Studio</Link> 创建一只</p>}
            <table className="w-full text-sm">
              <tbody>
                {data.my_agents.map((a) => (
                  <tr key={a.agent_id} data-agent={a.agent_id} className="border-b border-gray-100">
                    <td className="py-1.5">
                      <Link to={`/agents/${a.agent_id}`} className="font-medium text-emerald-700 hover:underline">{a.name}</Link>
                      <span className="ml-2 font-mono text-[10px] text-gray-400">{a.agent_id}</span>
                    </td>
                    <td className="py-1.5 text-xs text-gray-500">{a.attestation_state === 'valid' ? '🟢 签章有效' : a.attestation_state === 'expiring' ? '🟡 将过期' : '🔴 失效'}</td>
                    <td className="py-1.5 text-xs text-gray-500">审计 {a.audit_count} 次</td>
                    <td className="py-1.5">{a.data_provenance !== 'real' && <SimulatedBadge nature={a.data_provenance as 'simulated'} />}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {/* 待我签批明细 */}
          {data.my_pending_sign.length > 0 && (
            <section data-testid="me-pending-list" className="rounded-lg border border-red-100 p-4">
              <h3 className="mb-2 text-sm font-semibold text-red-800">签批待办明细</h3>
              {data.my_pending_sign.map((r) => (
                <div key={r.request_id} className="border-b border-red-50 py-1.5 text-xs text-gray-600">
                  <span className="font-mono">{r.request_id}</span> · {r.agent_id} · {r.urgency === 'urgent' ? '🔴 紧急' : r.urgency ?? '普通'} · {r.reason}
                </div>
              ))}
            </section>
          )}

          {/* 我批过的 + 沙盒 + 治理（三栏） */}
          <section className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            <div data-testid="me-decided" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-800">我批过的</h3>
              {data.my_decided.length === 0 && <p className="text-xs text-gray-400">暂无记录</p>}
              {data.my_decided.map((r) => (
                <div key={r.request_id} className="border-b border-gray-50 py-1 text-xs text-gray-600">
                  <span className="font-mono">{r.request_id}</span> · {r.status === 'approved' ? '✅ 批准' : r.status === 'rejected' ? '❌ 拒绝' : r.status}
                </div>
              ))}
            </div>
            <div data-testid="me-sandbox" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-800">我的沙盒申请</h3>
              {data.my_sandbox.length === 0 && <p className="text-xs text-gray-400">暂无申请</p>}
              {data.my_sandbox.map((a) => (
                <div key={a.apply_id} className="border-b border-gray-50 py-1 text-xs text-gray-600">
                  <span className="font-mono">{a.apply_id}</span> · {RESULT_LABEL[a.result ?? 'pending'] ?? a.result}
                </div>
              ))}
            </div>
            <div data-testid="me-governance" className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-800">我的治理操作</h3>
              {data.my_governance.length === 0 && <p className="text-xs text-gray-400">暂无操作</p>}
              {data.my_governance.map((g, i) => (
                <div key={i} className="border-b border-gray-50 py-1 text-xs text-gray-600">
                  {g.op === 'huf_sign' ? '✍️ HUF 签批' : '🛑 紧急熔断'} {g.fuse_state ? `· ${g.fuse_state}` : ''}
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </PageShell>
  )
}
