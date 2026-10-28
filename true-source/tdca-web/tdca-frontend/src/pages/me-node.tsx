// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI178 私域三空间（负空间／沙盒出盒／正空间）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI178-SITE-PRIVATE-ZONE-002 §一~§五——三件样张照做；
//   披露强制（不披露不可启用＋原因旁注）／六项硬核只读锁定（灰底虚线框＋锁标＋无输入控件）／
//   页顶流程条写死五步／样例态数据（虚构样例，标数据性质）／零接口零后端写入
// =============================================================================
import { useState } from 'react'
import { Link } from 'react-router'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

type SpaceKey = 'neg' | 'sandbox' | 'pos'

const TABS: { key: SpaceKey; label: string }[] = [
  { key: 'neg', label: '负空间' },
  { key: 'sandbox', label: '沙盒出盒' },
  { key: 'pos', label: '正空间' },
]

/** 流程条写死（样张原文，⛔ 不增删步） */
const FLOW_STEPS = ['私域改动', '生成待披露条目', '披露（落存证，可追谁在何时披露哪一版）', '回写版本号', '域内生效']

/** 负空间判据（虚构样例，样例态） */
const NEG_CRITERIA = [
  { name: '负空间零容忍判据（一类）', version: '第 3 版', effect: '待启用', disclosed: false },
  { name: '否决动作留痕判据', version: '第 2 版', effect: '已启用', disclosed: true },
  { name: '越界即停判据', version: '第 1 版', effect: '已启用', disclosed: true },
]

/** 沙盒出盒条件（虚构样例） */
const SANDBOX_CONDITIONS = [
  { cond: '门槛：三次演练通过', status: '启用中', trace: '10-27 由 节点管理员 调整门槛（留痕号 YJ-1027-03）' },
  { cond: '证据：演练留痕＋复核签字', status: '启用中', trace: '10-21 创建（留痕号 YJ-1021-01）' },
  { cond: '复核：双复核员会签', status: '已停用', trace: '10-26 由 域内复核员（甲）停用（留痕号 YJ-1026-02）' },
]

/** 正空间内部制度条目（虚构样例） */
const POS_ITEMS = [
  { name: '域内会议纪要与决议模板使用约定', version: '第 2 版' },
  { name: '域内知识库分层上架约定', version: '第 5 版' },
  { name: '域内值班与响应约定', version: '第 1 版' },
]

/** 六项硬核（只读锁定 · 三栏共同展示；H1~H6 为制度项编号，照条例机读版不剥） */
const HARDCORE = [
  { id: 'H1', title: '人类签名权不可绕过', desc: '关键动作须本人签，智能体不代签' },
  { id: 'H2', title: 'NCA 存证义务', desc: '每步留痕可追，无存证不执行' },
  { id: 'H3', title: '负空间否决不可关闭', desc: '否决本身不可停用' },
  { id: 'H4', title: '沙盒出盒门槛不可下调', desc: '门槛只可保持或加严' },
  { id: 'H5', title: '结算与税收口径照在册', desc: '界面上不自定费率与税基' },
  { id: 'H6', title: '数据性质必标', desc: '真实／模拟／合成，每条必标来源性质' },
]

export function MeNodePage() {
  // 三栏切换：纯页内状态（样例态，⛔ localStorage、⛔ 接口）
  const [space, setSpace] = useState<SpaceKey>('neg')

  return (
    <PageShell
      title="场景节点管理区（私域三空间）"
      dataSource="纯前端样例态（页内状态）；零接口调用、零后端写入"
      permission="须登录（谁的数据谁可见）"
      description="私域三空间：负空间／沙盒出盒／正空间。不披露不可启用；六项硬核只读锁定；示例节点与条目均为虚构样例。"
    >
      <div data-testid="me-node-page" className="space-y-6">
        {/* 入口卡（照样张入口件：第一屏与三空间入口） */}
        <section data-testid="me-node-entry" className="rounded-xl border border-gray-200 bg-white p-6">
          <div className="mb-2 flex flex-wrap gap-2">
            <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs text-red-700">私域 · 须登录</span>
            <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600">三空间</span>
            <SimulatedBadge nature="simulated" />
          </div>
          <h3 className="text-lg font-bold text-gray-900">私域三空间 ＋ 公域披露</h3>
          <p className="mt-1 text-xs text-gray-500">
            依据：私域三空间施工交办令（样张已由创始人亲验通过，照做施工）。本页为进私域后的第一屏与三空间入口。
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <a href="#me-node-spaces" data-testid="me-node-entry-spaces"
               className="rounded-lg bg-[#1a56db] px-5 py-2.5 text-sm text-white hover:bg-[#1746b3]">
              私域三栏（负空间／沙盒出盒／正空间）↓
            </a>
            <Link to="/disclosure" data-testid="me-node-entry-disclosure"
                  className="rounded-lg border border-[#1a56db] bg-white px-5 py-2.5 text-sm text-[#1a56db] hover:bg-blue-50">
              公域披露页（匿名可查）→
            </Link>
          </div>
          <ul className="mt-5 list-inside list-disc space-y-1 text-xs leading-relaxed text-gray-600">
            <li>「不披露不可启用」可辨：未披露条目的「启用」为不可用态并注明原因；</li>
            <li>六项硬核以只读锁定形态展示，无「关闭负空间否决」类开关；</li>
            <li>界面文字零内部编号形态；</li>
            <li>示例数据均为虚构样例，不指向真实在册件。</li>
          </ul>
        </section>

        {/* 页头条：场景节点管理区（私域 · 登录后） */}
        <div data-testid="me-node-header" className="flex flex-wrap items-center gap-3 rounded-lg bg-gray-800 px-5 py-3 text-white">
          <strong className="text-sm">场景节点管理区（私域 · 登录后）</strong>
          <span className="rounded-md bg-gray-700 px-3 py-1 text-xs">节点：示例节点·青屿（虚构样例）</span>
          <SimulatedBadge nature="simulated" />
        </div>

        {/* 流程条（写死，照样张原文） */}
        <div data-testid="me-node-flow" className="flex flex-wrap items-center gap-2 rounded-lg border border-orange-200 bg-orange-50 px-4 py-2.5 text-[13px] text-orange-800">
          <b className="whitespace-nowrap">流程写死：</b>
          {FLOW_STEPS.map((s, i) => (
            <span key={s} className="flex items-center gap-2">
              <span className="rounded-md border border-orange-300 bg-white px-2.5 py-0.5">{s}</span>
              {i < FLOW_STEPS.length - 1 && <span className="text-orange-500">→</span>}
            </span>
          ))}
        </div>

        {/* 三栏（主件 · 照样张甲） */}
        <section id="me-node-spaces" data-testid="me-node-spaces">
          <div className="flex gap-1.5" role="tablist" aria-label="私域三空间">
            {TABS.map((t) => (
              <button
                key={t.key}
                role="tab"
                aria-selected={space === t.key}
                data-testid={`me-node-tab-${t.key}`}
                onClick={() => setSpace(t.key)}
                className={`rounded-t-lg border border-b-0 border-gray-300 px-5 py-2 text-sm ${
                  space === t.key ? 'bg-white font-semibold text-gray-900' : 'bg-gray-200 text-gray-600'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* 负空间 */}
          {space === 'neg' && (
            <div data-testid="me-node-panel-neg" role="tabpanel" className="rounded-b-lg rounded-tr-lg border border-gray-300 bg-white p-5">
              <button className="mb-3 rounded-md bg-[#1a56db] px-3 py-1.5 text-xs text-white">＋ 新增判据条目</button>
              <table className="w-full border-collapse text-[13px]">
                <thead>
                  <tr>
                    {['判据名称', '版本', '生效状态', '披露状态', '操作'].map((h) => (
                      <th key={h} className="border border-gray-200 bg-gray-50 px-2.5 py-2 text-left font-semibold text-gray-700">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {NEG_CRITERIA.map((c) => (
                    <tr key={c.name}>
                      <td className="border border-gray-200 px-2.5 py-2">{c.name}</td>
                      <td className="border border-gray-200 px-2.5 py-2">{c.version}</td>
                      <td className={`border border-gray-200 px-2.5 py-2 font-semibold ${c.disclosed ? 'text-emerald-700' : 'text-amber-700'}`}>
                        {c.effect}
                      </td>
                      <td className={`border border-gray-200 px-2.5 py-2 ${c.disclosed ? 'font-semibold text-emerald-700' : 'text-gray-400'}`}>
                        {c.disclosed ? '已披露（存证可查）' : '未披露'}
                      </td>
                      <td className="border border-gray-200 px-2.5 py-2">
                        <button className="mr-1 rounded-md border border-[#1a56db] bg-white px-3 py-1 text-xs text-[#1a56db]">编辑</button>
                        {/* 披露强制：未披露 → 启用不可用（disabled）＋原因旁注 */}
                        <button
                          disabled={!c.disclosed}
                          data-testid={c.disclosed ? undefined : 'me-node-enable-blocked'}
                          title="须先披露"
                          className="mr-1 rounded-md border border-gray-300 bg-gray-200 px-3 py-1 text-xs text-gray-400 disabled:cursor-not-allowed"
                        >
                          启用
                        </button>
                        <button className="rounded-md border border-[#1a56db] bg-white px-3 py-1 text-xs text-[#1a56db]">改前→改后</button>
                        {!c.disclosed && (
                          <span className="mt-0.5 block text-xs text-amber-700">「启用」不可用原因：须先披露（不披露不可启用）</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {/* 改前→改后（样张对照区） */}
              <div data-testid="me-node-diff" className="mt-3 grid grid-cols-[1fr_40px_1fr] gap-2.5">
                <div className="whitespace-pre-wrap rounded-lg border border-gray-200 bg-gray-50 p-3 text-[13px] text-gray-700">
                  <b>改前（第 2 版）</b>{'\n'}触发即记录：越界行为写入留痕。
                </div>
                <div className="self-center text-center text-xl text-gray-400">→</div>
                <div className="whitespace-pre-wrap rounded-lg border border-green-200 bg-green-50 p-3 text-[13px] text-gray-700">
                  <b>改后（第 3 版 · 待披露）</b>{'\n'}触发即记录：越界行为写入留痕；留痕含动作人、时点、依据判据三项。
                </div>
              </div>
            </div>
          )}

          {/* 沙盒出盒 */}
          {space === 'sandbox' && (
            <div data-testid="me-node-panel-sandbox" role="tabpanel" className="rounded-b-lg rounded-tr-lg border border-gray-300 bg-white p-5">
              <div className="mb-3 grid grid-cols-1 gap-3 md:grid-cols-3">
                <div>
                  <label className="mb-1 block text-xs text-gray-600" htmlFor="pz-sb-threshold">门槛项（可设）</label>
                  <input id="pz-sb-threshold" defaultValue="沙盒内连续三次演练通过"
                         className="w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-[13px]" />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-600" htmlFor="pz-sb-evidence">证据要求（可设）</label>
                  <input id="pz-sb-evidence" defaultValue="附演练留痕与复核签字"
                         className="w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-[13px]" />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-gray-600" htmlFor="pz-sb-reviewer">复核人（可设）</label>
                  <select id="pz-sb-reviewer" defaultValue="节点管理员"
                          className="w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-[13px]">
                    <option>节点管理员</option>
                    <option>域内复核员（甲）</option>
                    <option>域内复核员（乙）</option>
                  </select>
                </div>
              </div>
              <button className="mb-3 rounded-md bg-[#1a56db] px-3 py-1.5 text-xs text-white">保存出盒条件</button>
              <table className="w-full border-collapse text-[13px]">
                <thead>
                  <tr>
                    {['出盒条件', '启用状态', '最近改动留痕'].map((h) => (
                      <th key={h} className="border border-gray-200 bg-gray-50 px-2.5 py-2 text-left font-semibold text-gray-700">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SANDBOX_CONDITIONS.map((c) => (
                    <tr key={c.cond}>
                      <td className="border border-gray-200 px-2.5 py-2">{c.cond}</td>
                      <td className={`border border-gray-200 px-2.5 py-2 ${c.status === '启用中' ? 'font-semibold text-emerald-700' : 'text-gray-400'}`}>
                        {c.status}
                      </td>
                      <td className="border border-gray-200 px-2.5 py-2 text-gray-600">{c.trace}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <ul className="mt-3 list-inside list-disc text-[13px] leading-relaxed text-gray-600">
                <li>留痕示例：谁在何时改了哪条、改前改后为何，逐条可追。</li>
              </ul>
            </div>
          )}

          {/* 正空间 */}
          {space === 'pos' && (
            <div data-testid="me-node-panel-pos" role="tabpanel" className="rounded-b-lg rounded-tr-lg border border-gray-300 bg-white p-5">
              <div className="mb-3 rounded-lg border border-amber-300 bg-amber-100 px-3.5 py-2.5 text-sm font-semibold text-amber-800">
                ⚠️ 本栏内容「仅域内生效」——未经披露，不构成对外依据。
              </div>
              <button className="mb-3 rounded-md bg-[#1a56db] px-3 py-1.5 text-xs text-white">＋ 新增内部制度条目</button>
              <table className="w-full border-collapse text-[13px]">
                <thead>
                  <tr>
                    {['内部制度条目', '版本', '操作'].map((h) => (
                      <th key={h} className="border border-gray-200 bg-gray-50 px-2.5 py-2 text-left font-semibold text-gray-700">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {POS_ITEMS.map((c) => (
                    <tr key={c.name}>
                      <td className="border border-gray-200 px-2.5 py-2">{c.name}</td>
                      <td className="border border-gray-200 px-2.5 py-2">{c.version}</td>
                      <td className="border border-gray-200 px-2.5 py-2">
                        <button className="mr-2 rounded-md border border-[#1a56db] bg-white px-3 py-1 text-xs text-[#1a56db]">编辑</button>
                        <span className="cursor-pointer text-sm text-red-600">删除</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* 六项硬核（只读锁定 · 三栏共同展示；⛔ 无输入控件、⛔ 无关闭类开关） */}
        <section data-testid="me-node-hardcore" className="rounded-xl border border-dashed border-gray-400 bg-gray-100 p-5">
          <h3 className="mb-1 text-sm font-semibold text-gray-700">🔒 六项硬核（只读锁定 · 三栏共同展示）</h3>
          <p className="mb-3 text-xs text-gray-500">
            只读区与可编辑区视觉可分：灰化＋锁标＋无输入控件；任何角色不可编辑；⛔ 不设「关闭负空间否决」类开关。六项全称照条例机读版。
          </p>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-3 xl:grid-cols-6">
            {HARDCORE.map((h) => (
              <div key={h.id} data-testid={`me-node-hc-${h.id}`}
                   className="rounded-lg border border-gray-300 bg-gray-200 p-2.5 text-center text-xs text-gray-500">
                🔒 {h.id}
                <br />
                <b className="text-gray-600">{h.title}</b>
                <br />
                {h.desc}
              </div>
            ))}
          </div>
        </section>
      </div>
    </PageShell>
  )
}
