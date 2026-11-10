// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI207 MYSPACE-PHASE1-001 §一.2 — 我的配置 /me/config（新建）
// 约束矩阵: §二-H-1/H-2/H-3；H-4 ⛔「一键发布」「跳过检查」类控件（本面只读，零写操作）；
//           §一.6 单件详情五态状态机展示
// 依据（H-3）: 配置记录为最小链要约留痕（dashboard note 原样）；处置依《配置权市场规范（单一权威稿·中文人读版V1.0（现行））》
// =============================================================================
import { useState } from 'react'
import { PageShell } from '@/components/PageShell'
import { PrivateGateNotice, usePrivateGate } from '@/components/PrivateGate'
import { FiveStateMachine } from '@/components/FiveStateMachine'
import { SimulatedBadge } from '@/lib/SimulatedBadge'
import { useApiGet } from '@/lib/useApi'

interface ConfigRow {
  run_id: string
  result: string
  asset_summary: string | null
  scene: string | null
  price_points: number | null
  nca_ref: string | null
  ts: string
}

interface MeDashboardConfig {
  my_config_records: ConfigRow[]
}

export function MeConfigPage() {
  const gate = usePrivateGate()
  const { status, data, nature } = useApiGet<MeDashboardConfig>('/api/v1/me/dashboard', undefined)
  const [openId, setOpenId] = useState<string | null>(null)

  if (gate !== 'ok') {
    return (
      <PageShell title="我的配置" dataSource="—" permission="须登录（谁的数据谁可见）"
                 description="区 2 四入口之一：我的配置。">
        <PrivateGateNotice state={gate} />
      </PageShell>
    )
  }

  return (
    <PageShell
      title="我的配置"
      dataSource="M5 GET /api/v1/me/dashboard（my_config_records 切片；与 /me 同账同源，零新后端）"
      permission="须登录（谁的数据谁可见）"
      description="区 2 四入口之一。本面只读：配置记录为最小链要约留痕；处置依《配置权市场规范（单一权威稿·中文人读版V1.0（现行））》。守门（区 4）与编译流水线（区 2A）随二批令，本面不设任何写操作。"
    >
      {nature && <div className="mb-2"><SimulatedBadge nature={nature} /></div>}
      {status === 'loading' && <p data-testid="me-config-loading" className="text-sm text-gray-400">加载中…</p>}
      {status === 'fail' && (
        <p data-testid="me-config-fail" className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          账本暂不可达（fail-closed）：未渲染任何配置数据，请稍后再试。
        </p>
      )}
      {status === 'ok' && data && (
        <div data-testid="me-config-list" className="space-y-2">
          {data.my_config_records.length === 0 && (
            <p data-testid="me-config-empty" className="text-sm text-gray-500">暂无配置记录（如实空表，未猜测）。</p>
          )}
          {data.my_config_records.map((r) => {
            const open = openId === r.run_id
            return (
              <div key={r.run_id} data-testid={`me-config-${r.run_id}`} className="rounded-lg border border-gray-200 bg-white">
                <button type="button" onClick={() => setOpenId(open ? null : r.run_id)}
                        data-testid={`me-config-toggle-${r.run_id}`}
                        className="flex w-full flex-wrap items-center gap-2 px-4 py-3 text-left">
                  <span className="font-mono text-xs text-gray-500">{r.run_id}</span>
                  <span className="text-sm font-medium text-gray-800">[{r.result}]</span>
                  {r.nca_ref && <span className="font-mono text-[11px] text-emerald-700">存证 {r.nca_ref}</span>}
                  <span className="ml-auto text-xs text-gray-400">{open ? '收起 ▲' : '详情 ▼'}</span>
                </button>
                {open && (
                  <div data-testid={`me-config-detail-${r.run_id}`} className="space-y-3 border-t border-gray-100 px-4 py-3">
                    <dl className="grid grid-cols-1 gap-2 text-sm md:grid-cols-2">
                      <div><dt className="text-xs text-gray-500">资产摘要</dt><dd>{r.asset_summary ?? '—'}</dd></div>
                      <div><dt className="text-xs text-gray-500">场景</dt><dd>{r.scene ?? '—'}</dd></div>
                      <div><dt className="text-xs text-gray-500">积分点</dt><dd>{r.price_points ?? '—'}</dd></div>
                      <div><dt className="text-xs text-gray-500">留痕时间</dt><dd className="font-mono">{r.ts?.slice(0, 19).replace('T', ' ')}</dd></div>
                      <div className="md:col-span-2"><dt className="text-xs text-gray-500">记录存证号（区 5 可查）</dt>
                        <dd className="font-mono">{r.nca_ref ?? '—（该记录暂无存证号，如实展示）'}</dd></div>
                    </dl>
                    {/* §一.6 五态状态机：一期骨架展示形态；配置记录未入编译管线，当前态无实据 */}
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
