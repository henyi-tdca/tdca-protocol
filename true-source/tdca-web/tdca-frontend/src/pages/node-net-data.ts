// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-FRONTEND-001 | 目标函数: 节点网络面 三处同源唯一数据源（NODE-NET-A-001 §四-8）
// 约束矩阵: 私域两卡、公域状态栏/可视图、后续转正表共读此件；无真值一律
//   「未设置／待复算／尚无」原句，⛔ 假数、⛔ 假节点、⛔ 内部编号进页面文案
// 取值依据: 条例件头与第 12/15 条（对外公开版 V1.0）；节点身份类字段实查无数据源 → 未设置
// =============================================================================

/** 已披露真节点（现仅创世节点一个——照令面与在册现状；⛔ 演示点、⛔ 占位名） */
export interface NodeView {
  name: string
  status: string
  heartbeat: string
  regulationVersion: string
  sink: string
  phase: string
  adaptation: string
}

export const NODES: NodeView[] = [
  {
    name: '创世节点',
    status: '运行中（以站点在架为据）',
    heartbeat: '尚无心跳 · 待节点首次上报',
    regulationVersion: 'V1.0',
    sink: '待复算',
    phase: '未设置',
    adaptation: '已适配',
  },
]

/** 可视图空位固定句（⛔ 占位名：其余位置一律此句） */
export const NODE_EMPTY_TEXT = '建设中 · 尚无其他节点接入'

/** 制度适配四态（图例同源） */
export const ADAPT_STATES = ['已适配', '待适配', '冲突·不可启用', '父级直承'] as const

/** 连线两态（图例同源） */
export const LINK_KINDS = ['制度同构', '未适配'] as const

/** 在册条例与契约（真值照条例件头；弃用期在册未列明 → 未设置） */
export const NODE_REGULATION = {
  name: '《业务端节点接入与同构契约条例》',
  version: 'V1.0',
  effect: '已生效 · 生效日 2026-10-17',
  humanSlug: 'TDCA-REG-NODE-ACCESS-001（对外公开版·V1.0）.md',
  machineSlug: 'TDCA-REG-NODE-ACCESS-001-COMPILED（对外公开版·V1.0）.yaml',
  contractVersion: 'V1.0（随条例冻结）',
  contractDeprecation: '未设置（在册未列明）',
  changelog: '暂无',
}

/** 九类接口（照条例第 12 条逐类一行；能不能用照第 14 条空壳禁止：未实现即未开放） */
export const NINE_APIS: { name: string; usable: boolean }[] = [
  { name: '加入／注册', usable: false },
  { name: '身份交换／协议加载', usable: false },
  { name: '名录／发现', usable: false },
  { name: '计量上报', usable: false },
  { name: '额度／配额', usable: false },
  { name: '令牌／锚定', usable: false },
  { name: '文档／协议包分发', usable: true }, // 唯一可用：条例人读/机读可下载
  { name: '心跳／状态', usable: false },
  { name: '存证回传／校验', usable: false },
]

/** 卡1「我的节点」本机字段（实查无节点配置/身份/指纹/首启数据源 → 未设置） */
export const MY_NODE = {
  nodeName: '未设置',
  identity: '创世节点',
  rootFingerprint8: '未设置',
  deployForm: '未设置',
  firstStart: '未设置',
  sink: '待复算',
  phase: '未设置',
}

/** 卡底固定句（令面原文） */
export const CARD_FOOTER = '本节点为分层最低层场景；制度不减项、门槛不降低。'
