// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI207 MYSPACE-PHASE1-001 §一.4 — 区 6 申诉 /me/appeal 补齐
// 约束矩阵: 事由／对象／诉求／附件四字段；状态：已提交／受理中／已裁定（三态展示）；
//           §三.4 无「上传全部资料」整包索取、标最小必填（照 GSEQ-7831 最小集）；
//           H-3 私域不简化（引制度件名）；H-4 ⛔一键发布/跳过检查类控件
// 口径（如实）: 受理与裁定通道随制度入站开通（GSEQ-7831 二批）；本期表单为站内登记骨架——
//   提交仅存于本会话（不入账、不产生存证号、不预置处置承诺），开通后接账 ⟹ 状
//   态机展示已提交/受理中/已裁定三态，当前件恒为「已提交（站内登记）」
// =============================================================================
import { useState } from 'react'
import { PageShell } from '@/components/PageShell'
import { PrivateGateNotice, usePrivateGate } from '@/components/PrivateGate'

interface AppealDraft {
  id: string
  reason: string
  target: string
  claim: string
  attachmentName: string
  ncaRef: string
  ts: string
}

let seq = 0

export function MeAppealPage() {
  const gate = usePrivateGate()
  const [reason, setReason] = useState('')
  const [target, setTarget] = useState('')
  const [claim, setClaim] = useState('')
  const [attachmentName, setAttachmentName] = useState('')
  const [ncaRef, setNcaRef] = useState('')
  const [items, setItems] = useState<AppealDraft[]>([])
  const [err, setErr] = useState('')

  const submit = () => {
    setErr('')
    if (!reason.trim() || !target.trim() || !claim.trim()) {
      setErr('最小必填三项未齐：事由／对象／诉求（照 GSEQ-7831 最小集；附件与关联存证号均为选填）。')
      return
    }
    seq += 1
    const draft: AppealDraft = {
      id: `APL-LOCAL-${String(seq).padStart(3, '0')}`,
      reason: reason.trim(), target: target.trim(), claim: claim.trim(),
      attachmentName, ncaRef: ncaRef.trim(), ts: new Date().toISOString(),
    }
    setItems((prev) => [draft, ...prev])
    setReason(''); setTarget(''); setClaim(''); setAttachmentName(''); setNcaRef('')
  }

  if (gate !== 'ok') {
    return (
      <PageShell title="申诉" dataSource="—" permission="须登录（谁的事谁可见）"
                 description="区 6：对惩罚处置（冻结／降权／吊销）的申诉。">
        <PrivateGateNotice state={gate} />
      </PageShell>
    )
  }

  return (
    <PageShell
      title="申诉"
      dataSource="站内登记（本会话态；受理/裁定通道随制度入站开通后接账，GSEQ-7831 二批）"
      permission="须登录（谁的事谁可见）"
      description="区 6。依《流程环节卡争议裁决（五问·七类失败·第17张卡）》与《TDCA注册登记制度（中文人读版V1.0（现行））》：受理范围、材料要件与办理时限以制度入站件为准；本站不整包索取资料，只收最小必填集。"
    >
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section data-testid="me-appeal-form" className="space-y-3 rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-gray-800">申诉登记（最小必填：事由／对象／诉求）</h3>
          <label className="block text-xs text-gray-600">
            事由 <span className="text-red-500">*</span>
            <textarea data-testid="me-appeal-reason" value={reason} onChange={(e) => setReason(e.target.value)} rows={3}
                      className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1 text-sm" />
          </label>
          <label className="block text-xs text-gray-600">
            对象（被申诉的处置/单据） <span className="text-red-500">*</span>
            <input data-testid="me-appeal-target" value={target} onChange={(e) => setTarget(e.target.value)}
                   className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1 text-sm" />
          </label>
          <label className="block text-xs text-gray-600">
            诉求 <span className="text-red-500">*</span>
            <textarea data-testid="me-appeal-claim" value={claim} onChange={(e) => setClaim(e.target.value)} rows={3}
                      className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1 text-sm" />
          </label>
          <label className="block text-xs text-gray-600">
            附件（选填；本期仅登记文件名，不传输、不整包索取）
            <input data-testid="me-appeal-attachment" type="file" onChange={(e) => setAttachmentName(e.target.files?.[0]?.name ?? '')}
                   className="mt-1 w-full text-xs" />
            {attachmentName && <span data-testid="me-appeal-attachment-name" className="mt-1 block text-[11px] text-gray-500">已登记文件名：{attachmentName}（未上传）</span>}
          </label>
          <label className="block text-xs text-gray-600">
            关联存证号（选填；可至 <a href="/me/nca" className="text-emerald-700 underline">区 5 存证查看</a> 回查）
            <input data-testid="me-appeal-nca" value={ncaRef} onChange={(e) => setNcaRef(e.target.value)}
                   className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1 font-mono text-sm" />
          </label>
          {err && <p data-testid="me-appeal-err" className="text-xs text-amber-700">{err}</p>}
          <button type="button" data-testid="me-appeal-submit" onClick={submit}
                  className="rounded-md border border-emerald-600 bg-emerald-600 px-3 py-1.5 text-sm text-white hover:bg-emerald-700">
            提交登记
          </button>
          <p className="text-[11px] text-gray-500">
            本期为站内登记骨架：提交仅存于本会话，不入账、不产生存证号；受理与裁定通道开通后接账（状态机三态见右）。
          </p>
        </section>

        <section data-testid="me-appeal-list" className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">登记记录（本会话）</h3>
          {/* 三态状态机展示（§一.4）：已提交 → 受理中 → 已裁定 */}
          <ol data-testid="me-appeal-states" className="mb-3 flex items-center gap-1 text-[11px]">
            {['已提交', '受理中', '已裁定'].map((s, i) => (
              <li key={s} className="flex items-center gap-1">
                <span className={i === 0 ? 'rounded border border-emerald-500 bg-emerald-50 px-2 py-0.5 font-semibold text-emerald-800'
                                         : 'rounded border border-gray-200 bg-gray-50 px-2 py-0.5 text-gray-400'}>
                  {s}
                </span>
                {i < 2 && <span className="text-gray-300">→</span>}
              </li>
            ))}
            <span className="ml-2 text-gray-400">当前件恒为「已提交（站内登记）」；后两态开通后由账本驱动</span>
          </ol>
          {items.length === 0 && (
            <p data-testid="me-appeal-empty" className="text-sm text-gray-500">本会话暂无登记（如实空表）。</p>
          )}
          <ul className="space-y-2">
            {items.map((it) => (
              <li key={it.id} data-testid={`me-appeal-${it.id}`} className="rounded-md border border-gray-100 bg-gray-50 p-3 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-gray-500">{it.id}</span>
                  <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[11px] text-emerald-800">已提交（站内登记）</span>
                  <span className="text-xs text-gray-400">{it.ts.slice(0, 19).replace('T', ' ')}</span>
                </div>
                <div className="mt-1 text-xs text-gray-600">事由:{it.reason}</div>
                <div className="mt-1 text-xs text-gray-600">对象:{it.target}</div>
                <div className="mt-1 text-xs text-gray-600">诉求:{it.claim}</div>
                {it.attachmentName && <div className="mt-1 text-[11px] text-gray-500">附件（仅登记名）:{it.attachmentName}</div>}
                {it.ncaRef && <div className="mt-1 font-mono text-[11px] text-emerald-700">关联存证号:{it.ncaRef}</div>}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </PageShell>
  )
}
