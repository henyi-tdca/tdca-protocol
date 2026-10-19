// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 乙案 P2 运维日志表单（/ops/logs）
// 约束矩阵: TDCA-HANDOFF-OPS-STORAGE-P2-001 §四；TDCA-TPL-OPS-LOG-001-MACHINE（键名 1:1）
// 复用: PageShell / api（会话令牌自动注入）；前端即时提示，后端 V-1~V-8 为准
// =============================================================================
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api } from '@/api/client'
import { PageShell } from './PageShell'

const NA = '无'
const GROUPS = ['A_基本信息', 'B_技术运维', 'C_内容运维', 'D_运营运维', 'E_安全合规', 'F_异常与收尾'] as const

interface ExItem {
  id: string; found_at: string; symptom: string; impact: string
  action: string; actor_role: string; closed: boolean; verify_method: string
  next_step: string; deadline: string
}

const PROBE_PATHS = ['/', '/ops', '/library', '/docs', '/api/v1/system/overview']
const STATUSES = [200, 401, 403, 404, 500, 502, 503]

function today08(): string {
  const d = new Date(Date.now() + (new Date().getTimezoneOffset() + 480) * 60000)
  return d.toISOString().slice(0, 10)
}

function emptySections(day: string) {
  return {
    A_基本信息: {
      date: day, duty_role: '', handover_role: '',
      checklist_done: { pre_deploy: false, daily: true, weekly: false, per_batch: true },
      backfill: { is_backfill: false, reason: '' },
    },
    B_技术运维: {
      root_http_status: 200,
      keypage_probe: PROBE_PATHS.map((path) => ({ path, status: 200 })),
      cert_not_after: '', cert_days_left: 0,
      acme_selftest: 'pass',
      service_health: { status: 'ok', abnormal_containers: NA },
      backup: { name: '', sha256_16: '', location: '' },
      swap_today: { done: false, build_tree: 'n/a', commit: 'n/a', smoke5: 'n/a', postcheck4: 'n/a' },
      tech_abnormal: false,
    },
    C_内容运维: {
      ingest_batch: { done: false, batch_id: NA, item_count: 0 },
      trail_seven_cols: '齐',
      reject_list: { hit_count: 0, empty_list_issued: true },
      content_probe: { checked_count: 5, abnormal: NA },
      bulletin: { state: NA, doc_id: NA, authorized: false },
      public_private_leak: { state: NA, location: NA, handled: true },
    },
    D_运营运维: {
      daily_patrol: { site_health: '正常', public_face: '正常', notify_machine: '正常', abnormal_log: NA },
      user_request_count: 0,
      appeal_count: { count: 0, pair_opened: true },
      assistant_to_human: { count: 0, forwarded: true },
    },
    E_安全合规: {
      three_maintain: { gate_open_state: '正常', robots_header: '在位', ops_401: '正常' },
      credential_change: { changed: false, changed_at: NA },
      security_event: { exists: false, event_id: NA, status: NA },
      redline_check: { zero_external: true, layering: true, no_semantic_ruling: true },
      crv_count: { handoff: 0, report: 0, witness: 0 },
    },
    F_异常与收尾: {
      exceptions: [] as ExItem[], carry_over: [] as string[], handover_next_day: [] as string[],
      filled_by: '', filled_at: '',
    },
  }
}

type Sections = ReturnType<typeof emptySections>

function T({ k, label, v, set, placeholder = '' }: {
  k: string; label: string; v: string | number
  set: (x: string) => void; placeholder?: string
}) {
  return (
    <label className="block text-xs" data-testid={`f-${k}`}>
      <span className="text-gray-600">{label}　</span>
      <input className="border rounded px-1 py-0.5 w-56" value={v} placeholder={placeholder}
        onChange={(e) => set(e.target.value)} />
    </label>
  )
}

function Cb({ k, label, v, set }: { k: string; label: string; v: boolean; set: (x: boolean) => void }) {
  return (
    <label className="inline-flex items-center gap-1 text-xs" data-testid={`f-${k}`}>
      <input type="checkbox" checked={v} onChange={(e) => set(e.target.checked)} />
      {label}
    </label>
  )
}

export function OpsLogsPage() {
  const [day, setDay] = useState(today08())
  const [dutyRole, setDutyRole] = useState('')
  const [dutyNo, setDutyNo] = useState('')
  const [handover, setHandover] = useState('')
  const [sec, setSec] = useState<Sections>(emptySections(today08()))
  const [carryText, setCarryText] = useState('')
  const [handoverText, setHandoverText] = useState('')
  const [msg, setMsg] = useState('')
  const [filledToday, setFilledToday] = useState<boolean | null>(null)

  useEffect(() => {
    void api.get<{ filled: boolean }>('/api/v1/ops/logs/today')
      .then((r) => { if (r.ok) setFilledToday(r.data.filled) })
  }, [])

  const setA = (patch: Partial<Sections['A_基本信息']>) =>
    setSec((s) => ({ ...s, A_基本信息: { ...s.A_基本信息, ...patch } }))
  const setB = (patch: Partial<Sections['B_技术运维']>) =>
    setSec((s) => ({ ...s, B_技术运维: { ...s.B_技术运维, ...patch } }))
  const setC = (patch: Partial<Sections['C_内容运维']>) =>
    setSec((s) => ({ ...s, C_内容运维: { ...s.C_内容运维, ...patch } }))
  const setD = (patch: Partial<Sections['D_运营运维']>) =>
    setSec((s) => ({ ...s, D_运营运维: { ...s.D_运营运维, ...patch } }))
  const setE = (patch: Partial<Sections['E_安全合规']>) =>
    setSec((s) => ({ ...s, E_安全合规: { ...s.E_安全合规, ...patch } }))

  const setEx = (i: number, patch: Partial<ExItem>) =>
    setSec((s) => {
      const exceptions = s.F_异常与收尾.exceptions.map((e, j) => (j === i ? { ...e, ...patch } : e))
      return { ...s, F_异常与收尾: { ...s.F_异常与收尾, exceptions } }
    })
  const addEx = () => setSec((s) => ({
    ...s, F_异常与收尾: { ...s.F_异常与收尾, exceptions: [...s.F_异常与收尾.exceptions, {
      id: `OPS-${day.replaceAll('-', '')}-${String(s.F_异常与收尾.exceptions.length + 1).padStart(2, '0')}`,
      found_at: '', symptom: '', impact: '', action: '', actor_role: '',
      closed: false, verify_method: '', next_step: '', deadline: '',
    }] },
  }))
  const rmEx = (i: number) => setSec((s) => ({
    ...s, F_异常与收尾: { ...s.F_异常与收尾, exceptions: s.F_异常与收尾.exceptions.filter((_, j) => j !== i) },
  }))

  const lines3 = (t: string) => t.split('\n').map((x) => x.trim()).filter(Boolean).slice(0, 3)

  const submit = async () => {
    setMsg('')
    const sections = {
      ...sec,
      A_基本信息: {
        ...sec.A_基本信息, date: day,
        duty_role: `${dutyRole}+${dutyNo}`, handover_role: handover,
      },
      F_异常与收尾: {
        ...sec.F_异常与收尾,
        carry_over: lines3(carryText), handover_next_day: lines3(handoverText),
        filled_by: `${dutyRole}+${dutyNo}`,
        filled_at: new Date().toISOString(),
      },
    }
    const r = await api.post('/api/v1/ops/logs', {
      duty_role: dutyRole, duty_no: dutyNo, handover, sections,
    })
    if (!r.ok) { setMsg(`入库被拒（后端校验为准）：${r.reason}`); return }
    setMsg('已入库（NCA 存证；同日同值日重复将被 409 拒绝）')
    setFilledToday(true)
  }

  const a = sec.A_基本信息, b = sec.B_技术运维, c = sec.C_内容运维
  const d = sec.D_运营运维, e = sec.E_安全合规, f = sec.F_异常与收尾

  return (
    <PageShell title="运维日志（每日填写）" dataSource="/api/v1/ops/logs（V-1~V-8 服务端校验）"
      permission="operator/founder（运维门内）"
      description="六组 A~F 照 TDCA-TPL-OPS-LOG-001-MACHINE 键名；异常三段（发现→处置→闭合）结构化成三格，未闭合必填下一步＋时限；不含口令/令牌/密钥字段。">
      <p className="text-xs">
        <Link to="/ops/logs/list" className="text-blue-600 underline">日志列表与导出 →</Link>
        <span className="ml-2 text-gray-400">周汇总/月报用导出 CSV（区间）。</span>
        {filledToday === false && <span data-testid="ops-logs-unfilled" className="ml-2 text-red-600">今日未填（红点）</span>}
        {filledToday === true && <span className="ml-2 text-green-600">今日已填</span>}
      </p>

      <section data-testid="ops-logs-form">
        <h2>A 基本信息</h2>
        <div className="flex flex-wrap gap-2 items-center">
          <T k="date" label="日期" v={day} set={(x) => { setDay(x); setSec((s) => ({ ...s, A_基本信息: { ...s.A_基本信息, date: x } })) }} placeholder="YYYY-MM-DD" />
          <T k="duty_role" label="值班角色" v={dutyRole} set={setDutyRole} placeholder="如 值班运维" />
          <T k="duty_no" label="工号" v={dutyNo} set={setDutyNo} placeholder="如 OP-001（勿填姓名）" />
          <T k="handover" label="交接人" v={handover} set={setHandover} placeholder="角色+工号" />
        </div>
        <div className="flex flex-wrap gap-3">
          <Cb k="pre_deploy" label="pre_deploy" v={a.checklist_done.pre_deploy} set={(x) => setA({ checklist_done: { ...a.checklist_done, pre_deploy: x } })} />
          <Cb k="daily" label="daily" v={a.checklist_done.daily} set={(x) => setA({ checklist_done: { ...a.checklist_done, daily: x } })} />
          <Cb k="weekly" label="weekly" v={a.checklist_done.weekly} set={(x) => setA({ checklist_done: { ...a.checklist_done, weekly: x } })} />
          <Cb k="per_batch" label="per_batch" v={a.checklist_done.per_batch} set={(x) => setA({ checklist_done: { ...a.checklist_done, per_batch: x } })} />
          <Cb k="backfill" label="补记" v={a.backfill.is_backfill} set={(x) => setA({ backfill: { ...a.backfill, is_backfill: x } })} />
          {a.backfill.is_backfill && (
            <T k="backfill_reason" label="补记原因" v={a.backfill.reason}
              set={(x) => setA({ backfill: { ...a.backfill, reason: x } })} />
          )}
        </div>

        <h2>B 技术运维</h2>
        <div className="flex flex-wrap gap-2 items-center">
          <label className="text-xs" data-testid="f-root_http_status">
            <span className="text-gray-600">根面状态　</span>
            <select className="border rounded" value={b.root_http_status}
              onChange={(ev) => setB({ root_http_status: Number(ev.target.value) })}>
              {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <T k="cert_not_after" label="证书到期" v={b.cert_not_after} set={(x) => setB({ cert_not_after: x })} placeholder="YYYY-MM-DD" />
          <T k="cert_days_left" label="余天数(实测)" v={b.cert_days_left} set={(x) => setB({ cert_days_left: Number(x) || 0 })} />
          <label className="text-xs" data-testid="f-acme_selftest">
            <span className="text-gray-600">ACME 自检　</span>
            <select className="border rounded" value={b.acme_selftest}
              onChange={(ev) => setB({ acme_selftest: ev.target.value })}>
              {['pass', 'fail', 'n/a'].map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
          <T k="svc_status" label="服务健康" v={b.service_health.status} set={(x) => setB({ service_health: { ...b.service_health, status: x } })} />
          <T k="svc_abnormal" label="异常容器" v={b.service_health.abnormal_containers} set={(x) => setB({ service_health: { ...b.service_health, abnormal_containers: x } })} />
          <Cb k="tech_abnormal" label="技术异常" v={b.tech_abnormal} set={(x) => setB({ tech_abnormal: x })} />
          <Cb k="swap_done" label="今日换发" v={b.swap_today.done}
            set={(x) => setB({ swap_today: { ...b.swap_today, done: x, ...(x ? {} : { build_tree: 'n/a', commit: 'n/a', smoke5: 'n/a', postcheck4: 'n/a' }) } })} />
          {b.swap_today.done && (
            <>
              <T k="swap_commit" label="commit" v={b.swap_today.commit} set={(x) => setB({ swap_today: { ...b.swap_today, commit: x } })} />
              <T k="swap_smoke5" label="smoke5" v={b.swap_today.smoke5} set={(x) => setB({ swap_today: { ...b.swap_today, smoke5: x } })} />
              <T k="swap_postcheck4" label="postcheck4" v={b.swap_today.postcheck4} set={(x) => setB({ swap_today: { ...b.swap_today, postcheck4: x } })} />
            </>
          )}
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <T k="backup_name" label="备份名" v={b.backup.name} set={(x) => setB({ backup: { ...b.backup, name: x } })} />
          <T k="backup_sha" label="sha256_16" v={b.backup.sha256_16} set={(x) => setB({ backup: { ...b.backup, sha256_16: x } })} />
          <T k="backup_loc" label="备份位" v={b.backup.location} set={(x) => setB({ backup: { ...b.backup, location: x } })} />
        </div>
        <div data-testid="f-keypage_probe">
          <p className="text-xs text-gray-600">关键页探针（≥5；改状态即可）</p>
          {b.keypage_probe.map((p, i) => (
            <label key={p.path} className="text-xs block">
              {p.path}　
              <select className="border rounded" value={p.status}
                onChange={(ev) => setB({
                  keypage_probe: b.keypage_probe.map((q, j) => (j === i ? { ...q, status: Number(ev.target.value) } : q)),
                })}>
                {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
          ))}
        </div>

        <h2>C 内容运维</h2>
        <div className="flex flex-wrap gap-2 items-center">
          <Cb k="ingest_done" label="有入站批" v={c.ingest_batch.done} set={(x) => setC({ ingest_batch: { ...c.ingest_batch, done: x, batch_id: x ? '' : NA } })} />
          {c.ingest_batch.done && (
            <>
              <T k="ingest_batch_id" label="批次号" v={c.ingest_batch.batch_id === NA ? '' : c.ingest_batch.batch_id} set={(x) => setC({ ingest_batch: { ...c.ingest_batch, batch_id: x } })} />
              <T k="ingest_count" label="件数" v={c.ingest_batch.item_count} set={(x) => setC({ ingest_batch: { ...c.ingest_batch, item_count: Number(x) || 0 } })} />
            </>
          )}
          <label className="text-xs" data-testid="f-trail_seven_cols">
            <span className="text-gray-600">七栏留痕　</span>
            <select className="border rounded" value={c.trail_seven_cols}
              onChange={(ev) => setC({ trail_seven_cols: ev.target.value })}>
              {['齐', '不齐', 'n/a'].map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
          <T k="reject_count" label="拒件数" v={c.reject_list.hit_count} set={(x) => setC({ reject_list: { ...c.reject_list, hit_count: Number(x) || 0 } })} />
          <Cb k="empty_list_issued" label="空清单已开" v={c.reject_list.empty_list_issued} set={(x) => setC({ reject_list: { ...c.reject_list, empty_list_issued: x } })} />
          <T k="probe_count" label="抽查数" v={c.content_probe.checked_count} set={(x) => setC({ content_probe: { ...c.content_probe, checked_count: Number(x) || 0 } })} />
          <T k="probe_abn" label="抽查异常" v={c.content_probe.abnormal} set={(x) => setC({ content_probe: { ...c.content_probe, abnormal: x } })} />
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <T k="bulletin_state" label="公告态" v={c.bulletin.state} set={(x) => setC({ bulletin: { ...c.bulletin, state: x } })} />
          <T k="bulletin_doc" label="公告件号" v={c.bulletin.doc_id} set={(x) => setC({ bulletin: { ...c.bulletin, doc_id: x } })} />
          <Cb k="bulletin_auth" label="已获明示" v={c.bulletin.authorized} set={(x) => setC({ bulletin: { ...c.bulletin, authorized: x } })} />
          <T k="leak_state" label="公私泄漏态" v={c.public_private_leak.state} set={(x) => setC({ public_private_leak: { ...c.public_private_leak, state: x } })} />
          <T k="leak_loc" label="位置" v={c.public_private_leak.location} set={(x) => setC({ public_private_leak: { ...c.public_private_leak, location: x } })} />
          <Cb k="leak_handled" label="已处置" v={c.public_private_leak.handled} set={(x) => setC({ public_private_leak: { ...c.public_private_leak, handled: x } })} />
        </div>

        <h2>D 运营运维</h2>
        <div className="flex flex-wrap gap-2 items-center">
          <T k="patrol_health" label="站健康" v={d.daily_patrol.site_health} set={(x) => setD({ daily_patrol: { ...d.daily_patrol, site_health: x } })} />
          <T k="patrol_public" label="公域面" v={d.daily_patrol.public_face} set={(x) => setD({ daily_patrol: { ...d.daily_patrol, public_face: x } })} />
          <T k="patrol_notify" label="通知机" v={d.daily_patrol.notify_machine} set={(x) => setD({ daily_patrol: { ...d.daily_patrol, notify_machine: x } })} />
          <T k="patrol_ablog" label="异常日志" v={d.daily_patrol.abnormal_log} set={(x) => setD({ daily_patrol: { ...d.daily_patrol, abnormal_log: x } })} />
          <T k="user_req" label="用户请求数(仅计数)" v={d.user_request_count} set={(x) => setD({ user_request_count: Number(x) || 0 })} />
          <T k="appeal_count" label="申诉数" v={d.appeal_count.count} set={(x) => setD({ appeal_count: { ...d.appeal_count, count: Number(x) || 0 } })} />
          <Cb k="appeal_pair" label="配对已开" v={d.appeal_count.pair_opened} set={(x) => setD({ appeal_count: { ...d.appeal_count, pair_opened: x } })} />
          <T k="asst_count" label="助手转办数" v={d.assistant_to_human.count} set={(x) => setD({ assistant_to_human: { ...d.assistant_to_human, count: Number(x) || 0 } })} />
          <Cb k="asst_fwd" label="已转人" v={d.assistant_to_human.forwarded} set={(x) => setD({ assistant_to_human: { ...d.assistant_to_human, forwarded: x } })} />
        </div>

        <h2>E 安全合规</h2>
        <div className="flex flex-wrap gap-2 items-center">
          <T k="m_gate" label="撤门态" v={e.three_maintain.gate_open_state} set={(x) => setE({ three_maintain: { ...e.three_maintain, gate_open_state: x } })} />
          <T k="m_robots" label="禁收录头" v={e.three_maintain.robots_header} set={(x) => setE({ three_maintain: { ...e.three_maintain, robots_header: x } })} />
          <T k="m_ops401" label="文件区401(四项维持)" v={e.three_maintain.ops_401} set={(x) => setE({ three_maintain: { ...e.three_maintain, ops_401: x } })} />
          <Cb k="cred_changed" label="凭据有变" v={e.credential_change.changed} set={(x) => setE({ credential_change: { changed: x, changed_at: x ? '' : NA } })} />
          {e.credential_change.changed && (
            <T k="cred_at" label="变更时点(勿记值)" v={e.credential_change.changed_at === NA ? '' : e.credential_change.changed_at}
              set={(x) => setE({ credential_change: { ...e.credential_change, changed_at: x } })} placeholder="时点即可，勿填值" />
          )}
          <Cb k="sec_event" label="安全事件" v={e.security_event.exists} set={(x) => setE({ security_event: { ...e.security_event, exists: x, event_id: x ? '' : NA } })} />
          {e.security_event.exists && (
            <>
              <T k="sec_id" label="事件号" v={e.security_event.event_id === NA ? '' : e.security_event.event_id} set={(x) => setE({ security_event: { ...e.security_event, event_id: x } })} />
              <T k="sec_status" label="状态" v={e.security_event.status === NA ? '' : e.security_event.status} set={(x) => setE({ security_event: { ...e.security_event, status: x } })} />
            </>
          )}
        </div>
        <div className="flex flex-wrap gap-3">
          <Cb k="rl_zero_ext" label="零对外" v={e.redline_check.zero_external} set={(x) => setE({ redline_check: { ...e.redline_check, zero_external: x } })} />
          <Cb k="rl_layering" label="分层无损" v={e.redline_check.layering} set={(x) => setE({ redline_check: { ...e.redline_check, layering: x } })} />
          <Cb key="rl_no_ruling" k="rl_no_ruling" label="不改判" v={e.redline_check.no_semantic_ruling} set={(x) => setE({ redline_check: { ...e.redline_check, no_semantic_ruling: x } })} />
        </div>

        <h2>F 异常与收尾</h2>
        <div data-testid="f-exceptions">
          {f.exceptions.map((ex, i) => (
            <fieldset key={ex.id} className="border rounded p-2 mb-2 text-xs" data-testid={`ex-${i}`}>
              <legend>{ex.id}</legend>
              <div className="flex flex-wrap gap-2 items-center">
                <T k={`ex${i}_found`} label="发现时点" v={ex.found_at} set={(x) => setEx(i, { found_at: x })} />
                <T k={`ex${i}_actor`} label="处置角色" v={ex.actor_role} set={(x) => setEx(i, { actor_role: x })} />
                <Cb k={`ex${i}_closed`} label="已闭合" v={ex.closed} set={(x) => setEx(i, { closed: x })} />
                {!ex.closed && (
                  <>
                    <T k={`ex${i}_next`} label="下一步(必填)" v={ex.next_step} set={(x) => setEx(i, { next_step: x })} />
                    <T k={`ex${i}_deadline`} label="时限(必填)" v={ex.deadline} set={(x) => setEx(i, { deadline: x })} />
                  </>
                )}
                <button type="button" onClick={() => rmEx(i)}>删此项</button>
              </div>
              <div className="grid grid-cols-3 gap-2 mt-1">
                <label className="block">发现（现象/影响）<textarea className="border rounded w-full" rows={2} value={`${ex.symptom}${ex.impact ? `\n影响：${ex.impact}` : ''}`} onChange={(ev) => { const [s, ...rest] = ev.target.value.split('\n影响：'); setEx(i, { symptom: s, impact: rest.join('\n影响：') || '' }) }} /></label>
                <label className="block">处置（action）<textarea className="border rounded w-full" rows={2} value={ex.action} onChange={(ev) => setEx(i, { action: ev.target.value })} /></label>
                <label className="block">闭合（verify_method）<textarea className="border rounded w-full" rows={2} value={ex.verify_method} onChange={(ev) => setEx(i, { verify_method: ev.target.value })} placeholder="未闭合填 未闭合" /></label>
              </div>
            </fieldset>
          ))}
          <button type="button" onClick={addEx}>＋ 添加异常项（三段：发现→处置→闭合）</button>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs mt-2">
          <label className="block">carry_over（≤3 行）<textarea className="border rounded w-full" rows={3} value={carryText} onChange={(ev) => setCarryText(ev.target.value)} /></label>
          <label className="block">handover_next_day（≤3 行）<textarea className="border rounded w-full" rows={3} value={handoverText} onChange={(ev) => setHandoverText(ev.target.value)} /></label>
        </div>

        <div className="mt-3 flex gap-2 items-center">
          <button data-testid="ops-logs-submit" onClick={submit}>提交日志</button>
          {msg && <span role="status">{msg}</span>}
        </div>
        <p className="text-xs text-gray-400 mt-1">键名与机读版模板同源（{GROUPS.join(' / ')}）；前端仅即时提示，V-1~V-8 以服务端为准。</p>
      </section>
    </PageShell>
  )
}
