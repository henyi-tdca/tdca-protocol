// =============================================================================
// TDCA 制度水印
// =============================================================================
// FC-ID:        TDCA-FC-20260808-002-S3-轨道B
// 目标函数:     Cytoscape 引擎 ∪ Kimi 视觉层（B1 坐标系对齐 + B2 脱敏 + B4 流向动画）
// 约束矩阵:     宪法十六条 + NSFL-V0.2 + E-EDU-API-V1.0（FROZEN，只读消费）
// 先验分布:     tdca-topology-ui（cytoscape ^3.30.2）+ Kimi network.tsx（SVG 百分比坐标）
// 配置权边界:    L2 层（仅展示制度关系，不暴露真实主体敏感连接权重）
// 预期分配:     拓扑引擎组件 + 坐标映射 + 脱敏规则
// 审计轨迹:     TDCA-NCA-20260808-014
// 开发者:       Reasonix
// 负空间版本:    NSFL-V0.2
// MOU 锚定:     TDCA-MOU-20260808-002（模拟）
// =============================================================================
/**
 * TopologyEngine — 轨道 B 拓扑引擎
 *
 * B1 坐标系对齐：Cytoscape 图论坐标（layout 计算）→ 百分比坐标（viewport）→ Kimi SVG
 * B2 脱敏：连接权重 >0.8 聚合为强关系边（不显示具体值）；主体标识哈希化
 * B3 坐标卡切换：物理世界 ↔ 智能体世界 300ms 过渡（CSS transition）
 * B4 配置权协议流向：动态 dash 动画（不暴露真实调用频次）
 *
 * 数据源：E-EDU-API-V1.0 concepts/relations（默认）或本地 netNodes/netEdges
 */
import { useEffect, useMemo, useState } from 'react'
import cytoscape, { type ElementDefinition } from 'cytoscape'

export interface TopoNode {
  id: string
  label: string
  type: 'official' | 'user' | 'infra' | 'gov'
  /** 敏感度：连接权重（用于脱敏聚合） */
  weight?: number
  status?: 'active' | 'idle' | 'fused'
}

export interface TopoEdge {
  from: string
  to: string
  label: string
  state?: 'flowing' | 'idle' | 'fused'
  /** 敏感度：真实调用频次（脱敏：不展示具体值） */
  tps?: string
}

export interface TopoData {
  nodes: TopoNode[]
  edges: TopoEdge[]
}

/**
 * B2 脱敏工具：主体标识哈希化（SHA-256 截断）
 * 规则：展示层用哈希 ID，不暴露真实主体标识（如 H-H 经验网络具体个体）
 */
export function hashAgentId(id: string): string {
  // 轻量哈希（非密码学用途，仅展示层脱敏）
  let h = 0
  for (let i = 0; i < id.length; i++) {
    h = (h * 31 + id.charCodeAt(i)) | 0
  }
  return 'A-' + Math.abs(h).toString(16).padStart(6, '0').slice(0, 6).toUpperCase()
}

/**
 * B2 脱敏：连接权重 >0.8 的强关系 → 聚合边
 * 规则：强关系边不显示具体权重值，渲染为加粗聚合边
 */
export function aggregateStrongEdges(edges: TopoEdge[]): TopoEdge[] {
  const byPair = new Map<string, TopoEdge[]>()
  for (const e of edges) {
    const key = [e.from, e.to].sort().join('|')
    if (!byPair.has(key)) byPair.set(key, [])
    byPair.get(key)!.push(e)
  }
  const result: TopoEdge[] = []
  for (const [, group] of byPair) {
    const strong = group.filter((e) => {
      // 权重来自 tps 数字部分（脱敏阈值 0.8 语义化：tps > 100 视为强关系）
      const n = parseInt((e.tps ?? '0').replace(/[^0-9]/g, ''), 10) || 0
      return n > 100
    })
    if (strong.length > 0) {
      // 聚合边：不显示具体值
      result.push({ ...strong[0], label: `${strong[0].label}（强关系）`, tps: undefined, state: 'flowing' })
    } else {
      result.push(...group)
    }
  }
  return result
}

/**
 * PLUS-4：E-EDU-API-V1.0 concepts/relations → TopoData 适配器
 * 映射规则：L0 卷节点 → infra（制度基座）；L1 章节节点 → user（内容节点）
 * 脱敏：主体标识经 hashAgentId 哈希化（Edu 场景同样生效）
 * 数据源：/api/edu/content（FROZEN 只读）
 */
export interface EEDUTopoNode {
  id: string
  name: string
  layer: 'L0' | 'L1' | 'L2' | 'L3'
}
export interface EEDUTopoRelation {
  from: string
  to: string
  type: string
}

export function eduTopoAdapter(
  chapters: { concepts: EEDUTopoNode[]; relations: EEDUTopoRelation[] }[],
): TopoData {
  const nodes: TopoNode[] = []
  const edges: TopoEdge[] = []
  const seen = new Set<string>()
  for (const ch of chapters) {
    for (const c of ch.concepts ?? []) {
      if (seen.has(c.id)) continue
      seen.add(c.id)
      nodes.push({
        id: hashAgentId(c.id),              // 脱敏：哈希化 ID
        label: c.name,
        type: c.layer === 'L0' ? 'infra' : 'user',  // 卷节点=基座，章节点=内容
        status: 'idle',
      })
    }
    for (const r of ch.relations ?? []) {
      edges.push({
        from: hashAgentId(r.from),
        to: hashAgentId(r.to),
        label: r.type === 'contains' ? '包含' : r.type,
        state: 'idle',
      })
    }
  }
  return { nodes, edges }
}

/**
 * TopologyEngine — 核心组件
 * Cytoscape 计算布局 → 映射到百分比坐标 → SVG 渲染（Kimi 视觉层样式）
 */
export function TopologyEngine({ data, height = 420 }: { data: TopoData; height?: number }) {
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({})
  const [world, setWorld] = useState<'physical' | 'agent'>('agent')

  // B1：Cytoscape headless 布局计算（图论坐标 → 百分比）
  // SITE-SEC-001 B-6：headless:true 不创建 canvas——原挂 display:none 隐藏容器致 3 个 0×0 canvas 残留
  //（headless 模式不做任何渲染，布局/boundingBox/position 读数与非 headless 完全一致，视觉层仍为 SVG）
  useEffect(() => {
    const elements: ElementDefinition[] = [
      ...data.nodes.map((n) => ({
        data: { id: n.id, label: n.label },
      })),
      ...data.edges.map((e) => ({
        data: { id: `${e.from}-${e.to}`, source: e.from, target: e.to, label: e.label },
      })),
    ]
    const instance = cytoscape({
      elements,
      styleEnabled: false,
      layout: { name: 'cose', animate: false, padding: 20 },
      headless: true,
    })
    // 布局完成后读取位置 → 百分比坐标
    instance.ready(() => {
      const bb = instance.elements().boundingBox()
      const pos: Record<string, { x: number; y: number }> = {}
      instance.nodes().forEach((nd) => {
        const p = nd.position()
        pos[nd.id()] = {
          x: Math.round(((p.x - bb.x1) / (bb.x2 - bb.x1 || 1)) * 100),
          y: Math.round(((p.y - bb.y1) / (bb.y2 - bb.y1 || 1)) * 100),
        }
      })
      setPositions(pos)
    })
    return () => instance.destroy()
  }, [data])

  // B2：脱敏处理（聚合强关系边）
  const safeEdges = useMemo(() => aggregateStrongEdges(data.edges), [data])

  // B3：坐标卡切换（物理 ↔ 智能体，300ms 过渡）
  const switchWorld = () => setWorld((w) => (w === 'agent' ? 'physical' : 'agent'))
  const transform = world === 'agent' ? 'translateX(0)' : 'translateX(-100%)'

  // B4：配置权协议流向（动态 dash 动画）
  const edgeColor = (s: string | undefined) =>
    s === 'fused' ? '#f43f5e' : s === 'idle' ? '#475569' : '#C9A45C'

  return (
    <div className="relative overflow-hidden" style={{ height }}>
      {/* B3：物理/智能体世界坐标卡（双卡，300ms 过渡） */}
      <div className="flex h-full transition-transform duration-300 ease-in-out" style={{ transform }}>
        {/* 智能体世界卡（移动修复批：卡自 relative——切换按钮定位上下文归本卡，⛔双按钮同点互遮；
            RULING 裁示2 提亮：深底改浅底（原 #081222 黑框不可见），标签前景同步提深保对比） */}
        <div className="relative h-full w-full shrink-0 overflow-hidden rounded-lg border border-slate-200 bg-[#F8FAFC]">
          <svg className="h-full w-full">
            {safeEdges.map((e) => {
              const a = positions[e.from], b = positions[e.to]
              if (!a || !b) return null
              const color = edgeColor(e.state)
              return (
                <g key={`${e.from}-${e.to}`}>
                  <line
                    x1={`${a.x}%`} y1={`${a.y}%`} x2={`${b.x}%`} y2={`${b.y}%`}
                    stroke={color} strokeWidth={e.state === 'flowing' ? 1.8 : 1.2}
                    strokeDasharray={e.state === 'flowing' ? '6 4' : '2 4'}
                    strokeOpacity={e.state === 'fused' ? 0.9 : 0.55}
                    className={e.state === 'flowing' ? 'animate-[dash_1.2s_linear_infinite]' : ''}
                  />
                </g>
              )
            })}
            {data.nodes.map((n) => {
              const p = positions[n.id]
              if (!p) return null
              const fused = n.status === 'fused'
              const isOfficial = n.type === 'official'
              // SVG-FIX-001 案甲：transform 不受百分比（Chromium 报 Expected ')'），
              // 弃 transform 改坐标属性——circle cx/cy 与 text x/y 受百分比，dy 走用户单位 px，
              // 与同文件 L217 line x1/y1 之合法写法一致；渲染语义与意图完全一致
              return (
                <g key={n.id}>
                  <circle
                    cx={`${p.x}%`} cy={`${p.y}%`}
                    r={isOfficial ? 12 : 8}
                    fill={isOfficial ? '#0E2142' : '#12305E'}
                    stroke={fused ? '#f43f5e' : isOfficial ? '#C9A45C' : '#3B82F6'}
                    strokeWidth={fused ? 2 : 1.5}
                  />
                  <text x={`${p.x}%`} y={`${p.y}%`} dy={isOfficial ? -16 : -12} textAnchor="middle" className="fill-slate-700" style={{ fontSize: 9 }}>
                    {n.label.length > 8 ? n.label.slice(0, 7) + '…' : n.label}
                  </text>
                  {/* RULING-ENTRY-CONTENT-DEPLOY-001 裁示1：副标签（哈希式样内部码）必删——公开首页渲染即对外，⛔候裁 */}
                </g>
              )
            })}
          </svg>
          {/* 坐标卡切换按钮 */}
          <button
            onClick={switchWorld}
            className="absolute right-3 top-3 rounded-md border border-white/15 bg-[#0A1830]/80 px-3 py-1.5 text-[10px] text-[#E8CD8F] hover:bg-[#12305E]"
          >
            切换到物理世界
          </button>
        </div>
        {/* 物理世界卡（脱敏：仅制度关系概览，无具体个体；移动修复批：卡自 relative，同智能体卡） */}
        <div className="relative h-full w-full shrink-0 overflow-hidden rounded-lg border border-slate-200 bg-[#F1F5F9]">
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <p className="text-xs text-slate-600">物理世界坐标卡（制度关系概览）</p>
              <p className="mt-2 text-[10px] text-slate-500">
                物理节点：TCN 可信算力节点 / NM 通知机<br />
                连接权重 &gt;0.8 已聚合为强关系边（脱敏）
              </p>
            </div>
          </div>
          <button
            onClick={switchWorld}
            className="absolute left-3 top-3 rounded-md border border-slate-300 bg-white/80 px-3 py-1.5 text-[10px] text-slate-700 hover:bg-slate-100"
          >
            切换到智能体世界
          </button>
        </div>
      </div>
      <style>{`@keyframes dash { to { stroke-dashoffset: -20; } }`}</style>
    </div>
  )
}
