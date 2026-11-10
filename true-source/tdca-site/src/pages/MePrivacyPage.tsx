// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI208 SEG2-B2-REFIRE-001 块 B — 数据开放四档与冲突告知
//           （TDCA-AMEND-DESIGN-L1SI207-MY-SPACE-001-AMEND-2，GSEQ-7829）
// 约束矩阵: §三 四档（默认 L1，L3 ⛔预勾选）；§四 合规三守；§五 冲突告知三选项
//           （文案照件内逐字，⛔静默降级/偷偷使用/默认放宽/反复纠缠）；
//           §六 四类分治；§七 留痕可核（撤回与删除可验证）
// 口径（如实）: 档位申明与提权记录本期存于本机（localStorage），后端持久化涉 schema 变更
//           按 S-2 先报再动；「撤回与删除可验证」以本机核验呈现，接账候后续令。
// =============================================================================
import { useEffect, useState } from 'react'
import { PageShell } from '@/components/PageShell'
import { PrivateGateNotice, usePrivateGate } from '@/components/PrivateGate'

type Tier = 'L0' | 'L1' | 'L2' | 'L3'

interface TierDef {
  tier: Tier
  name: string
  can: string
  keep: string
  fit: string
}

const TIERS: TierDef[] = [
  { tier: 'L0', name: '全封闭', can: '⛔ 任何读取', keep: '不接', fit: '仅在用户自办（M-1 自助）时可行' },
  { tier: 'L1', name: '单次会话内可用（默认）', can: '本次编译可读；会话结束即失效', keep: '不留存', fit: '大多数情形' },
  { tier: 'L2', name: '授权期内可读', can: '在授权期内多次编译可复用', keep: '留存至撤回', fit: '反复编译者' },
  { tier: 'L3', name: '可沉淀', can: '可形成可复用资产模板供本人复用', keep: '留本人', fit: '须单独勾选＋二次确认' },
]

const GUARDS = [
  '合法合规：用户自证有权提供（不侵他人权属、不含违法内容）；上传第三方权属内容须单独告警；上传前声明确认、留痕',
  '合理脱敏利用：官方工具接触原文前即做脱敏（个人身份信息／凭据密钥／第三方权属标识／商业秘密标记／内部编号族五类）；仅用脱敏后内容参与编译',
  '保密：⛔ 对外披露、⛔ 入仓、⛔ 用于训练第三方模型、⛔ 跨用户复用（L3 亦仅限本人）',
]

const FOUR_KINDS = [
  { kind: '知识资产', example: '文稿、图示、数据集', rule: '可成版权标的；登记前 ⛔ 公开' },
  { kind: '业务数据', example: '自有数据库、客户名单', rule: '⛔ 入仓；输出仅聚合结果' },
  { kind: '个人敏感信息', example: '身份证件、联系方式', rule: '默认 L0 处理＋强制脱敏' },
  { kind: '第三方权属内容', example: '他人作品、上游代码', rule: '上传即告警：须自证有权；⛔ 未经许可用于编译' },
]

interface NoticeRecord {
  service: string
  choice: 'A' | 'B' | 'C'
  ts: string
}

const LS_TIER = 'me.data-tier'
const LS_NOTICES = 'me.tier-notices'

export function MePrivacyPage() {
  const gate = usePrivateGate()
  const [tier, setTier] = useState<Tier>('L1')
  const [picked, setPicked] = useState(false)
  const [l3Confirm, setL3Confirm] = useState(false)
  const [service, setService] = useState('反复编译（向导代做）')
  const [dataType, setDataType] = useState('私有知识库／数据库')
  const [noticeChoice, setNoticeChoice] = useState<'A' | 'B' | 'C' | ''>('')
  const [records, setRecords] = useState<NoticeRecord[]>([])
  const [verifyText, setVerifyText] = useState('')

  useEffect(() => {
    try {
      const t = localStorage.getItem(LS_TIER)
      if (t === 'L0' || t === 'L1' || t === 'L2' || t === 'L3') setTier(t)
      const r = localStorage.getItem(LS_NOTICES)
      if (r) setRecords(JSON.parse(r))
    } catch { /* 本机存储不可用则保持会话态 */ }
  }, [])

  const declare = (t: Tier) => {
    if (t === 'L3' && !l3Confirm) return
    setTier(t)
    setPicked(true)
    try { localStorage.setItem(LS_TIER, t) } catch { /* 会话态 */ }
  }

  const choose = (c: 'A' | 'B' | 'C') => {
    setNoticeChoice(c)
    const rec: NoticeRecord = { service, choice: c, ts: new Date().toISOString() }
    const next = [rec, ...records].slice(0, 50)
    setRecords(next)
    try { localStorage.setItem(LS_NOTICES, JSON.stringify(next)) } catch { /* 会话态 */ }
  }

  const verifyDelete = () => {
    try {
      localStorage.removeItem(LS_TIER)
      localStorage.removeItem(LS_NOTICES)
    } catch { /* 会话态 */ }
    setTier('L1')
    setPicked(false)
    setRecords([])
    setVerifyText('已执行：本机档位与提权记录已清除，重新进入本页读数为默认档 L1、记录数 0——删除可验证。')
  }

  if (gate !== 'ok') {
    return (
      <PageShell title="数据开放档位" dataSource="—" permission="须登录（谁的事谁可见）"
                 description="区 2：用户知识与数据之开放分档、合规脱敏与冲突告知。">
        <PrivateGateNotice state={gate} />
      </PageShell>
    )
  }

  const tierName = (t: Tier) => TIERS.find((x) => x.tier === t)?.name ?? t

  return (
    <PageShell title="数据开放档位（区 2）" dataSource="本机申明（骨架期）＋在册口径" permission="须登录"
               description="开放程度由用户选择（默认 L1）；官方工具接触私料须合法合规＋合理脱敏＋保密三守；档位不足必告知三选项。">
      <div className="space-y-4">
        {/* 四档申明 */}
        <section data-testid="privacy-tiers" className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">开放程度四档（默认 L1；L3 ⛔ 预勾选）</h3>
          <div className="grid gap-2 sm:grid-cols-2">
            {TIERS.map((t) => (
              <div key={t.tier} data-testid={`tier-${t.tier}`}
                   className={`rounded-md border p-3 text-xs ${tier === t.tier ? 'border-emerald-500 bg-emerald-50' : 'border-gray-200 bg-white'}`}>
                <div className="font-medium text-gray-800">{t.tier} · {t.name}</div>
                <p className="mt-1 text-gray-600">官方工具可：{t.can}</p>
                <p className="text-gray-600">留存：{t.keep}</p>
                <p className="text-gray-500">适用：{t.fit}</p>
                {t.tier === 'L3' && (
                  <label className="mt-1 flex items-center gap-2 text-gray-600">
                    <input type="checkbox" data-testid="tier-l3-confirm" checked={l3Confirm}
                           onChange={(e) => setL3Confirm(e.target.checked)} />
                    单独勾选＋二次确认（⛔ 预勾选）
                  </label>
                )}
                <button type="button" data-testid={`tier-pick-${t.tier}`}
                        disabled={t.tier === 'L3' && !l3Confirm}
                        onClick={() => declare(t.tier)}
                        className="mt-2 rounded-md border border-emerald-600 px-2 py-0.5 text-emerald-700 hover:bg-emerald-50 disabled:cursor-not-allowed disabled:border-gray-300 disabled:text-gray-300">
                  申明为本档
                </button>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[11px] text-gray-400" data-testid="tier-current">
            当前档：{tier}（{tierName(tier)}）{picked ? '· 已申明' : '· 默认'}。任何档可随时撤回＋删除，且删除可验证。本期申明存于本机，后端持久化涉 schema 变更按 S-2 先报再动。
          </p>
        </section>

        {/* 合规三守 */}
        <section data-testid="privacy-guards" className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">合规三守（每档皆适用）</h3>
          <ol className="list-inside list-decimal space-y-1 text-xs text-gray-700">
            {GUARDS.map((g) => <li key={g}>{g}</li>)}
          </ol>
        </section>

        {/* 冲突告知（档位不足必出三选项） */}
        <section data-testid="privacy-conflict" className="rounded-lg border border-amber-200 bg-amber-50/50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">冲突告知（档位不足＋服务不可避免须接触私料时必现）</h3>
          <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
            <label className="text-gray-600">服务名：<input data-testid="conflict-service" value={service} onChange={(e) => setService(e.target.value)} className="rounded border border-gray-300 px-1" /></label>
            <label className="text-gray-600">数据类型：<input data-testid="conflict-data" value={dataType} onChange={(e) => setDataType(e.target.value)} className="rounded border border-gray-300 px-1" /></label>
          </div>
          <blockquote data-testid="conflict-copy" className="rounded-md border border-amber-300 bg-white p-3 text-xs text-gray-700">
            你当前把私料设为【{tier}】。要完成「{service}」，官方工具需要读取你的 {dataType}。你可以：① 仅就本次提权让它办（办完即回落）；② 不办此项（你将无法获得 {service} 之结果）；③ 改为自助／人工方式（工具不读取你的数据）。⛔ 我们不会在你未选择时读取或使用。
          </blockquote>
          <div className="mt-2 flex flex-wrap gap-2">
            <button type="button" data-testid="conflict-choose-a" onClick={() => choose('A')}
                    className="rounded-md border border-emerald-600 px-2 py-0.5 text-xs text-emerald-700 hover:bg-emerald-50">A · 仅就本次提权（限该项·限本次·期满自动回落）</button>
            <button type="button" data-testid="conflict-choose-b" onClick={() => choose('B')}
                    className="rounded-md border border-gray-500 px-2 py-0.5 text-xs text-gray-600 hover:bg-gray-50">B · 不办此项（明确列出将无法获得之结果）</button>
            <button type="button" data-testid="conflict-choose-c" onClick={() => choose('C')}
                    className="rounded-md border border-blue-600 px-2 py-0.5 text-xs text-blue-700 hover:bg-blue-50">C · 改自助／人工（工具不接触私料）</button>
          </div>
          <p className="mt-1 text-[11px] text-gray-400" data-testid="conflict-result">
            {noticeChoice === 'A' && '已选 A：服务可办；提权限本次、限该项，期满自动回落并留痕。'}
            {noticeChoice === 'B' && `已选 B：保持原档 ${tier}，放弃「${service}」——你将无法获得该项结果。一次问清、记录在案，⛔ 反复纠缠。`}
            {noticeChoice === 'C' && '已选 C：转 M-1 自助或人工渠道，工具不接触私料；门槛升高但数据不出私域。'}
          </p>
          <ul data-testid="conflict-records" className="mt-2 space-y-0.5 text-[11px] text-gray-500">
            {records.map((r, i) => (
              <li key={i}>{r.ts}（+08 另计）·「{r.service}」选 {r.choice === 'A' ? '提权办此项' : r.choice === 'B' ? '不办此项' : '改人工／自助'}</li>
            ))}
          </ul>
        </section>

        {/* 四类分治 */}
        <section data-testid="privacy-kinds" className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">用户上传物四类分治</h3>
          <table className="w-full text-xs text-gray-700">
            <thead><tr className="text-left text-gray-400"><th className="py-1">类</th><th>例</th><th>特别要求</th></tr></thead>
            <tbody>
              {FOUR_KINDS.map((k) => (
                <tr key={k.kind} className="border-t border-gray-100">
                  <td className="py-1 font-medium">{k.kind}</td><td>{k.example}</td><td>{k.rule}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* 撤回与删除可验证 */}
        <section data-testid="privacy-withdraw" className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">撤回与删除（可验证）</h3>
          <button type="button" data-testid="privacy-delete-verify" onClick={verifyDelete}
                  className="rounded-md border border-red-500 px-2 py-0.5 text-xs text-red-600 hover:bg-red-50">
            撤回授权并删除本机接入记录
          </button>
          <p data-testid="privacy-verify-result" className="mt-2 text-xs text-gray-600">{verifyText || '删除后此处给出核验读数（档位回落 L1、记录清零可见）。'}</p>
        </section>
      </div>
    </PageShell>
  )
}
