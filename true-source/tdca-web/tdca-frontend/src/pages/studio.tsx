// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: F3 /studio Agent Studio（生命周期看板 + 创建向导 + 化合衍生 + HUF）
// 约束矩阵: FRAMEWORK-001 §七（生命周期界面）+ §8B.2（出盒终裁）+ ID91（化合 NCA 链继承）+ F-4/HUF
// 复用: LifecycleDashboard（LifecycleTimeline/DetailPanel/NCAChain/ExportButton）+ TopologyEngine
// =============================================================================
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { PageShell } from './PageShell'
import { SimulatedBadge } from '@/shared/SimulatedBadge'
import { HufModal } from '@/shared/guards'
import { LifecycleTimeline, DetailPanel, NCAChain, ExportButton, type LifecycleNode } from '@/components/LifecycleDashboard/LifecycleDashboard'
import { TopologyEngine, hashAgentId, type TopoData } from '@/components/workbuddy/TopologyEngine'

// ---- 生命周期六阶段（诞生→教育→沙盒→市场→化合衍生；F3 模拟数据）----
const LIFECYCLE_NODES: LifecycleNode[] = [
  { step: 'BIRTH', label: '诞生', status: 'ok', detail: { tdid: 'TDID-AGENT-007', creator: 'H（人类）' }, nca_ref: 'Meta-Attestation-NCA-001' },
  { step: 'EDU', label: '教育', status: 'ok', detail: { course: 'E-EDU 商学院', progress: '100%' }, nca_ref: 'NCA-EDU-001' },
  { step: 'SANDBOX', label: '沙盒', status: 'ok', detail: { sea: '4/5 GREEN', activation: 1.35 }, nca_ref: 'NCA-SBX-001' },
  { step: 'MARKET', label: '市场', status: 'ok', detail: { mou: 1200, calls: 3 }, nca_ref: 'NCA-MKT-001' },
  { step: 'COMPOUND', label: '化合衍生', status: 'pending', detail: { child: 'TDID-AGENT-007-C1' } },
]

const NCA_CHAIN = ['Meta-Attestation-NCA-001', 'NCA-EDU-001', 'NCA-SBX-001', 'NCA-MKT-001']

// ---- 创建向导五步（FRAMEWORK-001 §7.2）----
// plain＝人话一句（TDCA-PLAN-SITE-UX-PLAIN-001 A3；解释层，⛔ 不替换在册术语）
const WIZARD_STEPS = [
  { key: 'intent', title: '意图声明', plain: '用大白话说清你想让这个智能体干什么。',
    desc: '自然语言描述创建意图 → 辅助智能体解析为六要素草稿' },
  { key: 'six', title: '六要素确认', plain: '把大白话翻译成机器可核验的六项指标（如目标函数＝它要优化什么）。',
    desc: 'objective_function / constraint_matrix / prior_distribution / config_boundary / expected_allocation / audit_trail（G-1 校验 + 最小化合检查）' },
  { key: 'nsfl', title: '场景约束 + NSFL', plain: '划定它不许碰的边界，越界即熔断。',
    desc: '场景约束声明 + 负空间边界（NSFL）' },
  { key: 'edu', title: '商学院培训/辅导', plain: '上岗前培训（可选），没达标会如实提示。',
    desc: '可选培训（tdca-ta）；未达标提示' },
  { key: 'huf', title: 'HUF 签署 → 沙盒', plain: '你签字＝你为它负全责；签完它进沙盒试用。',
    desc: '签署 Config-Right-Token → 沙盒（SEA 五要件）→ 出盒终裁（/attestation/meta）' },
]

// ---- 化合衍生拓扑（父→子 NCA 链，ID91 继承）----
const COMPOUND_TOPO: TopoData = {
  nodes: [
    { id: hashAgentId('TDID-AGENT-007'), label: '父体 AGENT-007', type: 'official', status: 'active' },
    { id: hashAgentId('TDID-AGENT-007-C1'), label: '子体 C1', type: 'user', status: 'active' },
    { id: hashAgentId('TDID-AGENT-007-C2'), label: '子体 C2', type: 'user', status: 'idle' },
  ],
  edges: [
    { from: hashAgentId('TDID-AGENT-007'), to: hashAgentId('TDID-AGENT-007-C1'), label: '化合（NCA 链继承）', state: 'flowing' },
    { from: hashAgentId('TDID-AGENT-007'), to: hashAgentId('TDID-AGENT-007-C2'), label: '化合（NCA 链继承）', state: 'flowing' },
  ],
}

const LIFE_ACTIONS = [
  { key: 'remodel', label: '重塑' },
  { key: 'sleep', label: '休眠' },
  { key: 'activate', label: '激活' },
  { key: 'logout', label: '注销' },
] as const

/** F3 Agent Studio：人主导的智能体全生命周期作业空间（写操作全部 HUF 伴随） */
export function StudioPage() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState<LifecycleNode | null>(null)
  const [wizardStep, setWizardStep] = useState(0)
  const [actionModal, setActionModal] = useState<string | null>(null)
  const [wizardModal, setWizardModal] = useState(false)

  return (
    <PageShell
      title="作业（智能体全生命周期）"
      dataSource="全生命周期 API + HUF 签批通道（模拟态）"
      permission="登录 DID + HUF 签批"
      description="智能体全生命周期：诞生→教育→沙盒→出盒终裁（/attestation/meta）→市场→化合衍生。"
    >
      <div className="space-y-5">
        {/* A1 人话定位条（UX-PLAIN-001；解释层，制度术语照在册） */}
        <section data-testid="studio-plain-intro" className="rounded-lg border border-blue-200 bg-blue-50/60 p-4 text-sm leading-6 text-gray-800">
          <strong>这一页能干什么：</strong>在这里创建一个属于你的智能体——说清楚意图 → 确认六要素 → 你亲手 HUF 签署为它负责 → 它进沙盒试用，出盒须过终裁后才能正式上岗。
          全程你主导，AI 只打下手；每一步的存证（NCA）都可事后核验。
        </section>

        {/* 生命周期看板（复用 LifecycleDashboard + 时间轴动画增强） */}
        <section data-testid="studio-lifecycle" className="rounded-lg border border-gray-200 p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-800">生命周期看板 · TDID-AGENT-007</h3>
            <ExportButton data={{ request_id: 'AGENT-007', nodes: LIFECYCLE_NODES, nca_chain: NCA_CHAIN }} />
          </div>
          <div className="lifecycle-anim" data-testid="lifecycle-anim">
            <LifecycleTimeline nodes={LIFECYCLE_NODES} onSelect={setSelected} />
          </div>
          {/* A2 状态灯图例（UX-PLAIN-001） */}
          <p className="mt-2 text-xs text-gray-600" data-testid="lifecycle-legend">
            状态灯图例：<span className="text-green-700">● 绿＝该阶段已通过</span>（如沙盒＝试用期通过）；
            <span className="text-amber-700">● 黄＝进行中/待办</span>。点任一阶段可看明细与它自己的存证号。
          </p>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            <DetailPanel node={selected} />
            <NCAChain chain={NCA_CHAIN} />
          </div>
          {/* 生命周期写操作（全部 HUF） */}
          <div className="mt-3 flex flex-wrap gap-2">
            {LIFE_ACTIONS.map((a) => (
              <button
                key={a.key}
                data-testid={`life-action-${a.key}`}
                className="rounded border border-blue-600 bg-blue-600 px-2.5 py-1 text-xs text-white hover:bg-blue-700"
                onClick={() => setActionModal(a.label)}
              >
                {a.label}（HUF）
              </button>
            ))}
          </div>
        </section>

        {/* 创建向导（五步，终点 → /attestation/meta） */}
        <section data-testid="studio-wizard" className="rounded-lg border border-blue-200 bg-blue-50/40 p-4">
          <h3 className="mb-2 text-sm font-semibold text-blue-800">创建向导（人主导，辅助智能体协助）</h3>
          <div className="mb-3 flex flex-wrap items-center gap-1.5">
            {WIZARD_STEPS.map((s, i) => (
              <span key={s.key} className="flex items-center gap-1 text-xs">
                <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${i <= wizardStep ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>
                  {i + 1}
                </span>
                <span className={i <= wizardStep ? 'font-medium text-blue-800' : 'text-gray-500'}>{s.title}</span>
                {i < WIZARD_STEPS.length - 1 && <span className="text-gray-300">→</span>}
              </span>
            ))}
          </div>
          <p className="mb-1 text-sm font-medium text-blue-900" data-testid="wizard-plain">
            {WIZARD_STEPS[wizardStep].plain}
          </p>
          <p className="mb-3 text-sm text-gray-700" data-testid="wizard-desc">
            {WIZARD_STEPS[wizardStep].desc}
          </p>
          <div className="flex items-center gap-2">
            {wizardStep > 0 && (
              <button data-testid="wizard-prev" className="rounded border border-gray-300 px-2.5 py-1 text-xs" onClick={() => setWizardStep((s) => s - 1)}>
                上一步
              </button>
            )}
            {wizardStep < WIZARD_STEPS.length - 1 ? (
              <button data-testid="wizard-next" className="rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700" onClick={() => setWizardStep((s) => s + 1)}>
                下一步
              </button>
            ) : (
              <button data-testid="wizard-huf" className="rounded bg-amber-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-700" onClick={() => setWizardModal(true)}>
                HUF 签署 Config-Right-Token → 沙盒
              </button>
            )}
          </div>
          {/* A4 签署后果说明（UX-PLAIN-001；措辞照智库更正：中性表述，不自造制度语） */}
          <p className="mt-2 text-xs text-gray-600" data-testid="wizard-huf-note">
            签署即生效；此后出盒须过终裁（/attestation/meta）。AI 无权替你签。
          </p>
        </section>

        {/* 化合衍生（父→子 NCA 链，ID91） */}
        <section data-testid="studio-compound" className="rounded-lg border border-gray-200 p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-800">化合衍生（六要素继承 + NCA 链继承）</h3>
            <SimulatedBadge nature="simulated" />
          </div>
          <TopologyEngine data={COMPOUND_TOPO} height={260} />
          {/* A5 人话一句（UX-PLAIN-001） */}
          <p className="mt-2 text-xs text-gray-600" data-testid="compound-plain">
            从这里能「生」出新智能体：六要素与存证链（NCA）继承父体——子体一出生就带着家谱，信用记录随链可查。
          </p>
          <p className="mt-1 text-xs text-gray-500">
            父体（PCM-LIVE）→ 选择化合场景 → 六要素继承 + 场景偏移 → 子体诞生（NCA 链继承父体）→ 自动进入生命周期起点。
          </p>
        </section>
      </div>

      {/* HUF 模态：创建（出盒）终点 */}
      <HufModal
        open={wizardModal}
        onOpenChange={setWizardModal}
        onConfirm={() => navigate('/attestation/meta')}
        title="HUF 签署 · Config-Right-Token"
        description="创建向导终点：签署后进入沙盒（SEA 五要件）→ 沙盒验证 → 出盒终裁（/attestation/meta）。AI 无权替代人类签批。"
      />
      {/* HUF 模态：生命周期写操作（重塑/休眠/激活/注销） */}
      <HufModal
        open={actionModal !== null}
        onOpenChange={(o) => setActionModal(o ? actionModal : null)}
        onConfirm={() => setActionModal(null)}
        title={`HUF 签批 · ${actionModal ?? ''}`}
        description={`生命周期操作「${actionModal ?? ''}」须人类最终签批（F-4/HUF）；AI 无权代行。`}
      />
    </PageShell>
  )
}
