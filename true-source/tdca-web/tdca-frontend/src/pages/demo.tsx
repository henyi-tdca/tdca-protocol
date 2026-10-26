// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: L1SI175-B25 · 体验期与模拟演示一页（批2.5）
// 约束矩阵: TDCA-HANDOFF-EXEC-L1SI175-B25-001（6189）——四块模拟（积分／钱包／结算／交付税收）
//   ＋免责三条；全部前端演示值（页内 useState，⛔ localStorage、⛔ 接口、⛔ 后端）
// 红线: 页头＋每块＋页尾三处模拟标识缺一不可；⛔ 任何金额字样（¥／￥／元／价格／档位／付费）
//   单位只用「积分」；示例比例须标 ⛔ 真实税率；零内部编号
// =============================================================================
import { useState } from 'react'
import { Link } from 'react-router'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'

/** 结算模拟：环销（A→B→C→A 抵消一圈）→ 净额（各节点只付差额）→ 定向支付（剩余流量定向） */
interface SettlementResult {
  gross: [string, string, number][] // 环销前列表
  cycle: string // 抵消说明
  net: [string, string, number][] // 净额
  directed: [string, string, number][] // 定向支付
}

/** 计税模拟：基数 → 应缴（示例比例）→ 留痕（模拟存证号） */
interface TaxResult {
  base: number
  ratioPct: number
  due: number
  receipt: string
}

const CREDIT_USES = ['看公开资产', '用自助验链', '走三问向导']

const DISCLAIMERS = [
  '本页所有数字为模拟值，不是你的真实资产，⛔ 可提现 / ⛔ 可交易。',
  '体验期站内功能免费；演示值不代表将来定价，也不算报价。',
  '真实钱包 / 充值 / 结算 / 税收 / 税务票据 均在三期实现，届时另立制度。',
]

export function DemoPage() {
  // 纯页内状态：刷新即复位，⛔ localStorage、⛔ 任何后端写入
  const [settlement, setSettlement] = useState<SettlementResult | null>(null)
  const [tax, setTax] = useState<TaxResult | null>(null)

  function runSettlement() {
    // 示例积分值（SIMULATED）：A→B 300，B→C 120，C→A 80；环销后 C→A 净付 A 20
    setSettlement({
      gross: [['A', 'B', 300], ['B', 'C', 120], ['C', 'A', 80]],
      cycle: 'A→B→C→A 抵消一圈：各节点环形流量互相抵销，只剩差额流动',
      net: [['A', '净收', 20], ['B', '净收', 180], ['C', '净付', 200]],
      directed: [['C', 'A', 20], ['C', 'B', 180]],
    })
  }

  function runTax() {
    const base = 500
    const ratioPct = 2 // 示例比例，⛔ 真实税率
    setTax({
      base,
      ratioPct,
      due: (base * ratioPct) / 100,
      receipt: `SIM-NCA-${String(Date.now()).slice(-8)}（模拟存证号，示例）`,
    })
  }

  return (
    <PageShell
      title="体验期与模拟演示"
      dataSource="纯前端演示值（页内状态）；零接口调用、零后端写入"
      permission="公开"
      description="把体验期有什么、演示区在演什么、什么是真什么是假，一页讲清。真实钱包、充值、结算、税收均在三期。"
    >
      <div data-testid="demo-page" className="space-y-6">
        {/* 页头模拟标识（三处之一，必显著） */}
        <p data-testid="demo-banner" className="rounded-lg border-2 border-purple-300 bg-purple-50 p-4 text-center text-sm font-bold text-purple-800">
          演示区 · 数据为模拟值 · 非真实交易
        </p>

        {/* 块 1：虚拟积分 */}
        <section data-testid="demo-credits" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            虚拟积分 <SimulatedBadge nature="simulated" />
          </h3>
          <p className="text-xs text-gray-700">
            剩余积分：<strong className="text-gray-900">1,200</strong>（示例值）
          </p>
          <p className="mt-1 text-xs text-gray-600">体验期站内功能免费，积分不换钱、不可提现。</p>
          <p className="mt-2 text-xs text-gray-600">
            积分能做什么：
          </p>
          <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-gray-600">
            {CREDIT_USES.map((u) => (
              <li key={u}>{u}</li>
            ))}
          </ul>
        </section>

        {/* 块 2：钱包 */}
        <section data-testid="demo-wallet" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            钱包 <SimulatedBadge nature="simulated" />
          </h3>
          <p className="text-xs text-gray-700">
            钱包内：积分 1,200 ／ 现金余额：<strong className="text-gray-900">三期开放</strong>
          </p>
          <p className="mt-1 text-xs text-gray-600">真实充值、提现、支付均在三期。</p>
        </section>

        {/* 块 3：结算中心（可点跑一次） */}
        <section data-testid="demo-settlement" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            结算中心 <SimulatedBadge nature="simulated" />
          </h3>
          <button
            data-testid="demo-run-settlement"
            onClick={runSettlement}
            className="mb-3 rounded bg-gray-800 px-3 py-1.5 text-xs text-white"
          >
            跑一次模拟结算
          </button>
          {settlement && (
            <div data-testid="settlement-result" className="space-y-3 text-xs text-gray-600">
              <div>
                <div className="mb-1 font-semibold text-gray-700">① 环销（抵消前列表示例，单位：积分）</div>
                <table className="w-full border-collapse">
                  <tbody>
                    {settlement.gross.map(([f, t, v]) => (
                      <tr key={`${f}-${t}`}>
                        <td className="border border-gray-200 px-2 py-1">{f} → {t}</td>
                        <td className="border border-gray-200 px-2 py-1 text-right">{v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="mt-1 text-gray-500">{settlement.cycle}</p>
              </div>
              <div>
                <div className="mb-1 font-semibold text-gray-700">② 净额（各节点只付差额）</div>
                <table className="w-full border-collapse">
                  <tbody>
                    {settlement.net.map(([who, dir, v]) => (
                      <tr key={who}>
                        <td className="border border-gray-200 px-2 py-1">{who}</td>
                        <td className="border border-gray-200 px-2 py-1">{dir}</td>
                        <td className="border border-gray-200 px-2 py-1 text-right">{v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <div className="mb-1 font-semibold text-gray-700">③ 定向支付（剩余流量定向，单位：积分）</div>
                <table className="w-full border-collapse">
                  <tbody>
                    {settlement.directed.map(([f, t, v]) => (
                      <tr key={`${f}-${t}`}>
                        <td className="border border-gray-200 px-2 py-1">{f} → {t}</td>
                        <td className="border border-gray-200 px-2 py-1 text-right">{v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-gray-500">这是沙盒模拟，不涉及任何真实资金。</p>
            </div>
          )}
        </section>

        {/* 块 4：交付税收（可点跑一次） */}
        <section data-testid="demo-tax" className="rounded-lg border border-gray-200 p-4">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
            交付税收 <SimulatedBadge nature="simulated" />
          </h3>
          <button
            data-testid="demo-run-tax"
            onClick={runTax}
            className="mb-3 rounded bg-gray-800 px-3 py-1.5 text-xs text-white"
          >
            跑一次模拟计税
          </button>
          {tax && (
            <div data-testid="tax-result" className="space-y-1.5 text-xs text-gray-600">
              <p>① 基数：模拟交易额 {tax.base} 积分</p>
              <p>② 应缴：示例比例 {tax.ratioPct}% → {tax.due} 积分</p>
              <p>③ 留痕：{tax.receipt}</p>
              <p className="font-semibold text-amber-700">示例比例，⛔ 真实税率</p>
              <p className="text-gray-500">真实税务与票据在三期。</p>
            </div>
          )}
        </section>

        {/* 页尾免责三条（三处之三，逐字） */}
        <footer data-testid="demo-disclaimers" className="rounded-lg border border-gray-200 bg-gray-50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-900">免责三条</h3>
          <ol className="list-inside list-decimal space-y-1 text-xs leading-relaxed text-gray-600">
            {DISCLAIMERS.map((d) => (
              <li key={d}>{d}</li>
            ))}
          </ol>
        </footer>

        {/* L1SI175-B26：一句一链，通往模拟演练区 */}
        <p data-testid="demo-b2-lab" className="text-center text-xs text-gray-600">
          想动手走一遍 → <Link to="/lab" className="text-purple-700 underline">模拟演练区</Link>
        </p>
      </div>
    </PageShell>
  )
}
