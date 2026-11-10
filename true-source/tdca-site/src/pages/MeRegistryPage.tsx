// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI207 MYSPACE-PHASE1-001 §一.2 — 我的权属登记 /me/registry（新建）
// 约束矩阵: §二-H-1/H-2/H-3 同 MeAssetPage；§一.6 单件详情页五态状态机展示（FiveStateMachine）
// 依据（H-3）: 登记口径依《TDCA注册登记制度（中文人读版V1.0（现行））》；登记存证（nca_ref）可回查区 5
// =============================================================================
import { useState } from 'react'
import { PageShell } from '@/components/PageShell'
import { SimulatedBadge } from '@/lib/SimulatedBadge'
import { PrivateGateNotice, usePrivateGate } from '@/components/PrivateGate'
import { FiveStateMachine } from '@/components/FiveStateMachine'
import { useApiGet } from '@/lib/useApi'

interface OwnershipRow {
  record_id: string
  work_title: string
  jurisdiction_branch: string
  status: string
  nca_ref: string | null
  data_provenance: string
  created_at: string
}

interface MeDashboardRegistry {
  my_ownership: OwnershipRow[]
}

/** 登记状态如实标注（P8a 既有口径 registered/amended/cancelled，⛔ 不映射为五态） */
const REG_STATUS: Record<string, string> = {
  registered: '🟢 已登记',
  amended: '🟡 已变更',
  cancelled: '⚫ 已注销',
}

export function MeRegistryPage() {
  const gate = usePrivateGate()
  const { status, data } = useApiGet<MeDashboardRegistry>('/api/v1/me/dashboard', undefined)
  const [openId, setOpenId] = useState<string | null>(null)

  if (gate !== 'ok') {
    return (
      <PageShell title="我的权属登记" dataSource="—" permission="须登录（谁的数据谁可见）"
                 description="区 2 四入口之一：我的权属登记。">
        <PrivateGateNotice state={gate} />
      </PageShell>
    )
  }

  return (
    <PageShell
      title="我的权属登记"
      dataSource="M5 GET /api/v1/me/dashboard（my_ownership 切片；与 /me 同账同源，零新后端）"
      permission="须登录（谁的数据谁可见）"
      description="区 2 四入口之一。登记口径依《TDCA注册登记制度（中文人读版V1.0（现行））》；登记存证号可持往区 5 回查。"
    >
      {status === 'loading' && <p data-testid="me-registry-loading" className="text-sm text-gray-400">加载中…</p>}
      {status === 'fail' && (
        <p data-testid="me-registry-fail" className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          账本暂不可达（fail-closed）：未渲染任何登记数据，请稍后再试。
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="me-registry-list" className="space-y-2">
          {data.my_ownership.length === 0 && (
            <p data-testid="me-registry-empty" className="text-sm text-gray-500">名下暂无登记记录（如实空表，未猜测）。</p>
          )}
          {data.my_ownership.map((r) => {
            const open = openId === r.record_id
            return (
              <div key={r.record_id} data-testid={`me-registry-${r.record_id}`} className="rounded-lg border border-gray-200 bg-white">
                <button type="button" onClick={() => setOpenId(open ? null : r.record_id)}
                        data-testid={`me-registry-toggle-${r.record_id}`}
                        className="flex w-full flex-wrap items-center gap-2 px-4 py-3 text-left">
                  <span className="font-medium text-gray-800">{r.work_title}</span>
                  <span className="text-xs text-gray-500">{REG_STATUS[r.status] ?? r.status}</span>
                  {r.nca_ref && <span className="font-mono text-[11px] text-emerald-700">存证 {r.nca_ref}</span>}
                  <span className="ml-auto text-xs text-gray-400">{open ? '收起 ▲' : '详情 ▼'}</span>
                </button>
                {open && (
                  <div data-testid={`me-registry-detail-${r.record_id}`} className="space-y-3 border-t border-gray-100 px-4 py-3">
                    <dl className="grid grid-cols-1 gap-2 text-sm md:grid-cols-2">
                      <div><dt className="text-xs text-gray-500">登记号</dt><dd className="font-mono">{r.record_id}</dd></div>
                      <div><dt className="text-xs text-gray-500">管辖分支</dt><dd>{r.jurisdiction_branch}</dd></div>
                      <div><dt className="text-xs text-gray-500">登记时间</dt><dd className="font-mono">{r.created_at?.slice(0, 19).replace('T', ' ')}</dd></div>
                      <div><dt className="text-xs text-gray-500">数据来源</dt>
                        <dd>{r.data_provenance !== 'real' && <SimulatedBadge nature={r.data_provenance as 'simulated'} />}</dd></div>
                      <div className="md:col-span-2"><dt className="text-xs text-gray-500">登记存证号（区 5 可查）</dt>
                        <dd className="font-mono">{r.nca_ref ?? '—（该登记暂无存证号，如实展示）'}</dd></div>
                    </dl>
                    {/* §一.6 五态状态机：登记件未入编译管线，当前态无实据 ⟹ 组件自陈未入管 */}
                    <FiveStateMachine current={null} />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </PageShell>
  )
}
