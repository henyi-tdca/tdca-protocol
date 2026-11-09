// =============================================================================
// TDCA 制度水印
// FC-ID: TDCA-FC-SITE-001 | 目标函数: MIGRATE 批1 — 构建时生成全站检索静态索引 JSON
// 约束矩阵: L1SI206 MIGRATE-B1-001（检索整块迁产线 ⛔迁产物；条目 ≥549；三族覆盖；
//   索引内容零内部编号；⛔ 不写回、⛔ 不改原文；产物落 public/search-index.json）
// 算法谱系: 自旧版 scripts/build-search-index.mjs 移植（L1SI177 SITE-FIND-CODE-001 批3），
//   排序/化名逐字保留（⛔ 不另写一套）；「栏目」源由旧版 PAGE_META 改为
//   本树 App.tsx 静态路由 ∩ 题名录（未迁面不入索引，防死链）。
// 名斜处置（L1SI206 批1 裁定，2026-11-09）：仓内编号存档／站机净名上架系智库既定双轨
//   （TDCA-ASSESS-L1SI205-REGS-TRIPARTITE-001 判基面清白），故白名单净名⟶仓盘编号名
//   以下列 RENAME_MAP 桥接（逐字照 TDCA-LIST-L1SI204-RIGHTS-NETNAME-001/002 之
//   「现名→建议净名」反向，并经仓盘 8e362f2d 实测全中 48/50）；url/slug/title 一律
//   用白名单净名（S-1 防断链＋对外零内部编号）。题名源：制度族取白名单净名（NETNAME 审定），
//   其余族照旧版 H1/display_name 解析——旧索引 20 条编号残留题名全在制度族，此改清零。
// SPDX-License-Identifier: TDCA-Internal
// =============================================================================
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..')
const GATEWAY = join(ROOT, 'true-source', 'tdca-web', 'gateway', 'public_docs_ops.py')
const DOCS = join(ROOT, 'docs')
const TERMS_YAML = join(ROOT, 'docs', 'terms', 'TDCA-TERMINOLOGY-REGISTRY-V1.0-EXPORT-20261027-151条机读快照.yaml')
const APP_TSX = join(ROOT, 'true-source', 'tdca-site', 'src', 'App.tsx')
const OUT_DIR = join(ROOT, 'true-source', 'tdca-site', 'public')
const OUT = join(OUT_DIR, 'search-index.json')

const FAMILY_DIRS = { regulation: 'regulations', whitepapers: 'whitepapers', papers: 'papers', 'cop-library': 'cop-library' }
const FAMILY_LABEL = { regulation: '制度', whitepapers: '白皮书', papers: '论文', 'cop-library': '素材' }
const FAMILY_ORDER = ['制度', '白皮书', '论文', '素材', '术语', '栏目']

// ---------------------------------------------------------------- 净名⟶盘名映射（制度族）
// 来源逐字：NETNAME-001（A 档 41 ＋ 已净名）／NETNAME-002（B 档四件终名）；
// 「配置权市场授权追认附记」映射仓内在档件 TDCA-SIGNOFF-CONFIGMARKET-AUTH-001-追认附记.md
// （旧版索引 precedent：旧索引制度族 49 条即索引此件；站上净名版为剥内部行之衍生件，仓未收）。
// 读盘时 fail-closed：映射目标缺失即计入 missing（非豁免则 exit 1）。
const RENAME_MAP_REG = {
  '配置权市场规范（单一权威稿·中文人读版V1.0（现行））.md': 'TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（单一权威稿·中文人读版V1.0-FROZEN）.md',
  '配置权市场规范（英文人读版V1.0（现行））.md': 'TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（英文人读版V1.0-FROZEN）.md',
  '配置权市场规范（机读版V1.0（现行））.yaml': 'TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（机读版V1.0-FROZEN）.yaml',
  'TDCA注册登记制度（中文人读版V1.0（现行））.md': 'TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（中文人读版V1.0-FROZEN）.md',
  'TDCA注册登记制度（英文人读版V1.0（现行））.md': 'TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（英文人读版V1.0-FROZEN）.md',
  'TDCA注册登记制度（机读版V1.0（现行））.yaml': 'TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（机读版V1.0-FROZEN）.yaml',
  '场景线相遇专章对外版单独件（V1.0已生效·十七条）.md': 'TDCA-PUB-CORPUS-059-场景线相遇专章对外版单独件（V1.0已生效·十七条·供站上替换旧草案版）.md',
  '可信协作宪法（对外可读版·V0.1·十条与序言四支柱）.md': 'TDCA-PUB-CORPUS-017-可信协作宪法（对外可读版·V0.1草案候选·十条与序言四支柱）.md',
  '可信协作宪法英文人读版（V0.1·十条与四支柱·逐条对应中文）.md': 'TDCA-PUB-CORPUS-043-Constitution-EN-可信协作宪法英文人读版（V0.1·十条与四支柱·逐条对应中文）.md',
  '可信协作宪法机读版（V0.1·十条与四支柱·与中文英文互见）.yaml': 'TDCA-PUB-CORPUS-044-Constitution-MACHINE-可信协作宪法机读版（V0.1·十条与四支柱·与中文英文互见）.yaml',
  '身份可信等级认定条例对外版.md': 'TDCA-PUB-CORPUS-029-卷二纯版第二批清理版重出-身份可信等级认定条例对外版（仅去符号·语义同028·六检通过）.md',
  '身份可信等级认定条例英文人读版（十六条·V1.0·逐条对应中文）.md': 'TDCA-PUB-CORPUS-045-IdentityTier-EN-身份可信等级认定条例英文人读版（十六条·V1.0·逐条对应中文）.md',
  '身份可信等级认定条例机读版（四档与判定次序与三态·V1.0·互见）.yaml': 'TDCA-PUB-CORPUS-046-IdentityTier-MACHINE-身份可信等级认定条例机读版（四档与判定次序与三态·V1.0·互见）.yaml',
  '智能体定义条例对外版（二十一条·V1.0已生效）.md': 'TDCA-PUB-CORPUS-030-卷二纯版第三批-智能体定义条例对外版（二十一条·V1.0已生效·六检通过·引用不重写）.md',
  '智能体定义条例英文人读版（二十一条·V1.0·逐条对应中文）.md': 'TDCA-PUB-CORPUS-047-AgentDefinition-EN-智能体定义条例英文人读版（二十一条·V1.0·逐条对应中文）.md',
  '智能体定义条例机读版（本体与创世与主体与效用与生命周期·V1.0互见）.yaml': 'TDCA-PUB-CORPUS-048-AgentDefinition-MACHINE-智能体定义条例机读版（本体与创世与主体与效用与生命周期·V1.0互见）.yaml',
  '流程环节卡发现（五问·六类失败·第4张卡）.md': 'TDCA-PUB-CORPUS-083-流程环节卡发现（五问·六类失败·第4张卡）.md',
  '流程环节卡相遇（五问·六类失败·第5张卡）.md': 'TDCA-PUB-CORPUS-084-流程环节卡相遇（五问·六类失败·第5张卡）.md',
  '流程环节卡握手（五问·七类失败·第6张卡）.md': 'TDCA-PUB-CORPUS-085-流程环节卡握手（五问·七类失败·第6张卡）.md',
  '流程环节卡签约（五问·七类失败·第7张卡）.md': 'TDCA-PUB-CORPUS-086-流程环节卡签约（五问·七类失败·第7张卡）.md',
  '流程环节卡交付（五问·七类失败·第8张卡）.md': 'TDCA-PUB-CORPUS-087-流程环节卡交付（五问·七类失败·第8张卡）.md',
  '流程环节卡验收（五问·七类失败·第9张卡）.md': 'TDCA-PUB-CORPUS-088-流程环节卡验收（五问·七类失败·第9张卡）.md',
  '卷四治理卷对外版（谁定规则与怎么改与怎么监督与争议边界·首件）.md': 'TDCA-PUB-CORPUS-090-卷四治理卷对外版（谁定规则与怎么改与怎么监督与争议边界·首件）.md',
  '卷五同构卷对外版（制度与技术同构与本体同构与场景嵌套·移植四步·边界四条）.md': 'TDCA-PUB-CORPUS-091-卷五同构卷对外版（制度与技术同构与本体同构与场景嵌套·移植四步·边界四条）.md',
  '卷六助手与入口对外版（三类入口与助手四步接入与代签红线）.md': 'TDCA-PUB-CORPUS-092-卷六助手与入口对外版（三类入口与助手四步接入与代签红线）.md',
  '惩罚三态与守门器对外纯版（二十五条与AB九条·V1.0已生效2026-10-16）.md': 'TDCA-PUB-CORPUS-069-惩罚三态与守门器对外纯版（二十五条与AB九条·V1.0已生效2026-10-16）.md',
  '租户与环境作用域凭证绑定条例对外纯版（三规则一通路一分层·V1.0已生效2026-09-25）.md': 'TDCA-PUB-CORPUS-070-租户与环境作用域凭证绑定条例对外纯版（三规则一通路一分层·V1.0已生效2026-09-25）.md',
  'IP版权资产评估管理办法对外纯版（三十一条齐·V1.0已生效2026-09-30）.md': 'TDCA-PUB-CORPUS-071-IP版权资产评估管理办法对外纯版（三十一条齐·V1.0已生效2026-09-30）.md',
  '制度治理规范对外纯版（六判据链）.md': 'TDCA-PUB-CORPUS-074-制度治理规范对外纯版（六判据链·英文待补）.md',
  '流程环节卡注册缔约（五问·七类失败·三句固定·第三张卡）.md': 'TDCA-PUB-CORPUS-058-流程环节卡注册缔约（五问·七类失败·三句固定·第三张卡）.md',
  '流程环节卡授权配置（五问·七类失败·第1张卡）.md': 'TDCA-PUB-CORPUS-101-流程环节卡授权配置（五问·七类失败·第1张卡补五问版）.md',
  '流程环节卡结算计税（五问·七类失败·第2张卡）.md': 'TDCA-PUB-CORPUS-102-流程环节卡结算计税（五问·七类失败·第2张卡补五问版）.md',
  '流程环节卡谈判（五问·七类失败·第10张卡）.md': 'TDCA-PUB-CORPUS-097-流程环节卡谈判（五问·七类失败·第10张卡）.md',
  '流程环节卡试错（五问·七类失败·第11张卡）.md': 'TDCA-PUB-CORPUS-098-流程环节卡试错（五问·七类失败·第11张卡）.md',
  '流程环节卡验证（五问·七类失败·第12张卡）.md': 'TDCA-PUB-CORPUS-099-流程环节卡验证（五问·七类失败·第12张卡）.md',
  '流程环节卡履约准备（五问·七类失败·第13张卡）.md': 'TDCA-PUB-CORPUS-100-流程环节卡履约准备（五问·七类失败·第13张卡）.md',
  '流程环节卡履约（五问·七类失败·第14张卡）.md': 'TDCA-PUB-CORPUS-093-流程环节卡履约（五问·七类失败·第14张卡）.md',
  '流程环节卡结算分配（五问·七类失败·第15张卡）.md': 'TDCA-PUB-CORPUS-094-流程环节卡结算分配（五问·七类失败·第15张卡）.md',
  '流程环节卡信用及遗产管理（五问·七类失败·第16张卡）.md': 'TDCA-PUB-CORPUS-095-流程环节卡信用及遗产管理（五问·七类失败·第16张卡）.md',
  '流程环节卡争议裁决（五问·七类失败·第17张卡）.md': 'TDCA-PUB-CORPUS-096-流程环节卡争议裁决（五问·七类失败·第17张卡）.md',
  '授权件模板对外版（中文人读·V1.0（现行）·八字段与四要件）.md': 'TDCA-PUB-CORPUS-103-授权件模板对外版（中文人读·V1.0-FROZEN按签批更正版本面貌·八字段与四要件）.md',
  '存证（NCA）制度·对外节选版（V1.1）.md': 'TDCA-PUB-NCA-STD-001-EXT-V1.1-存证（NCA）制度对外节选版（已生效·与内部V1.1同版·差异清单）-R2.md',
  '官方可信认知资产登记·创世认知资产区块（V1.0·已登记）.md': 'TDCA-PUB-NCA-GENESIS-REG-001-TDCA官方可信认知资产登记·创世认知资产区块（人读·已登记·对外节选版）.md',
  '业务端节点接入与同构契约条例（对外公开版·V1.0）.md': 'TDCA-REG-NODE-ACCESS-001（对外公开版·V1.0）.md',
  '业务端节点接入与同构契约条例（机读版·对外公开版·V1.0）.yaml': 'TDCA-REG-NODE-ACCESS-001-COMPILED（对外公开版·V1.0）.yaml',
  '配置权市场授权追认附记.md': 'TDCA-SIGNOFF-CONFIGMARKET-AUTH-001-追认附记.md',
  // MIGRATE 批2补件入仓（TDCA-HANDOFF-EXEC-L1SI206-CORPUS104-001）：白名单在册而仓内无源→补件
  '人机协作工作条例.md': 'TDCA-PUB-CORPUS-104-人机协作工作条例（V1.0已生效）.md',
}
// 豁免缺件（⛔ 静默跳过）：白名单在册而仓内无源，逐件须有据并回报挂账。
// 2026-11-09：人机协作工作条例已补件入仓（PUB-CORPUS-104），豁免条清零。
const EXEMPT_MISSING = {
}
const resolveDiskName = (famKey, entry) =>
  famKey === 'regulation' ? (RENAME_MAP_REG[entry] ?? entry) : entry

// ---------------------------------------------------------------- 栏目题名录（fail-closed）
// 题名著者：本树 PAGE_META（/ /overview /about /pages /announcements）＋ -188 对照表同路径题名
// ＋本树新增面实读。脚本断言：App.tsx 每条静态路由必须在本表有题名，否则 throw（防漏维护）。
// 动作页（/auth /register）与检索页自身（/search）不入栏目索引（照旧版口径）。
const COLUMN_TITLES = {
  '/': '首页 · 三体可视化中心',
  '/overview': '制度总览 · 四层架构',
  '/about': '关于 · 一页看懂 TDCA',
  '/pages': '站点地图',
  '/announcements': '公告栏',
  '/me': '个人后台（我的）',
  // MIGRATE 批7（L1SI206）：申诉面迁入（旧版权 me-appeal 直拷；须登录但照 /me 惯例入栏目索引）
  '/me/appeal': '申诉（对惩罚处置：冻结／降权／吊销）',
  '/review': '评审（缔约审核）',
  '/docs': '文档库',
  '/agents': '智能体集群观测',
  '/agent-shelf': '智能体区（组二 10 件呈现）',
  '/studio': '作业（智能体全生命周期）',
  '/workbuddy': '人机协作工作台',
  '/ownership': '所有权市场（L1 法定确权层）',
  '/ownership-registry': '权属登记管理（P8a）',
  '/authorization-registry': '合约备案（P8b）',
  '/attestation': '确权中心总览',
  '/attestation/meta': '元函数初始确权（出盒终裁）',
  '/attestation/dynamic': '动态确权请求队列',
  '/attestation/history': '确权历史',
  '/anchors': '模拟外部锚与版权事件（P6）',
  '/audit': '审计透明',
  '/governance': '治理中心',
  '/formal': '形式化与实验线结论入站（P3）',
  '/cluster': '集群编排与准入闸门（P2）',
  '/market': '配置权市场（L2）',
  '/market-sim': '规范索引与沙盒最小链（P9）',
  '/tax': '税收仪表盘（L3 效用计量）',
  '/library': '内容区文库（白皮书 · 论文 · 产物库 · 法律原文 · 适用说明）',
  '/academy': 'TDCA 商学院',
  '/toolshelf': '工具货架（P4）',
  '/notifier': '通知机状态页',
  '/sandbox': '沙盒准入（L2 前置反应釜）',
  '/ops': '站点运维端（P7）',
  '/process': '流程总览（协作流程 14 环）',
  '/registrations': '权属登记查询（公域）',
  '/channel/portal': '智能体通道 · 门户总览',
  '/channel/agents': '智能体通道 · 集群接入',
  '/channel/registry': '智能体通道 · 登记指引',
  '/channel/market': '智能体通道 · 市场接入',
  '/channel/tools': '智能体通道 · 工具接入',
  // MIGRATE 批2（L1SI206）：通道两面迁入，题名取登记净名（仓盘编号存档双轨）
  '/channel/my': '我的通道（智能体四步流水线）',
  '/channel/register': '智能体自助登记（通道登记）',
  // MIGRATE 批3（L1SI206）：严选与节点八面＋/channel 总入口迁入，题名照 route-parity.md 旧版题名栏
  '/channel': '智能体通道',
  '/curation': '严选池 · 精选项目一栏',
  '/contribute': '我要贡献 · 三级台阶',
  '/public-face': '匿名可见面',
  '/private': '私域与边界 · 公域守门人',
  '/nodes': '节点网络',
  '/me/node': '场景节点管理区（私域三空间）',
  '/me/node/net': '我的节点 · 条例与契约',
  '/disclosure': '节点规则披露登记簿 · 公域可查',
  // MIGRATE 批4（L1SI206）：演练与实验两面迁入，题名照旧版页头（同栈直拷）
  '/lab': '模拟演练区',
  '/demo': '体验期与模拟演示',
  // MIGRATE 批6（L1SI206）：入门与指南两面迁入，题名照旧版页头（/start 为公开指引面入栏目索引）
  '/start': '新手指引 · 六步上手 TDCA',
  '/nca-guide': '存证（NCA）说明',
}
// MIGRATE 批5（L1SI206）：运维手册三界面（README/OPS/CHANGELOG）⛔入栏目索引（私域隔离红线——
// 令面 §三.2「内容⛔入检索索引」；照旧版动作页豁免口径，路由可达但不收录不题名）
// 用组批（L1SI206-USE-GROUP-B1）：「用」组两面（U-1 交素材／U-2 代办登记）⛔入栏目索引——
// 登录动作面，照 /auth /register 旧版动作页豁免口径（路由可达、两页互链、不收录不题名）
const COLUMN_EXCLUDE = new Set(['/auth', '/register', '/search', '/ops/readme', '/ops/ops', '/ops/changelog', '/use/upload', '/use/agent'])

// 编号形态禁则（旧版施工令 §三.2；TAIL-CLEAN-001 块A：title/summary/body 共用本表）
// B1 追加（硬约束第8条「索引内容零内部编号」，旧表未覆盖 registry 件号形态，旧索引曾残留 20 条）：
//   TDCA-…-NNN _registry 件号（SPEC/PUB-CORPUS/PUB-NCA/REG-NODE-ACCESS/SIGNOFF/TEMPLATE-AUTH/STD/RULING/EVID 等）
//   与裸 PUB-CORPUS-NNN（件号头行）。站机公开名 TDCA-OPS-NN（两位号）不在剥除列，保留。
const FORBIDDEN = [/\bCOP-\d+\b/gi, /\bGSEQ-\d+\b/g, /(^|[^A-Z0-9])A-\d+(?![0-9])/g, /\bT-\d{3}\b/g, /base_protocol/gi,
  /\bTDCA-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}\b/g, /\bPUB-CORPUS-\d+\b/g]
const stripForbidden = (s) => {
  let out = s
  for (const re of FORBIDDEN) out = out.replace(re, '')
  return out.replace(/-{2,}/g, '-').replace(/\s{2,}/g, ' ').trim()
}
const slugFromEntry = (entry) =>
  stripForbidden(entry.split('/').pop().replace(/\.(md|yaml)$/, '')).replace(/^-+|-+$/g, '')
const isForbiddenToken = (t) => FORBIDDEN.some((re) => {
  re.lastIndex = 0
  return re.test(t)
})

const latinTokens = (s) => {
  const toks = s.match(/[A-Za-z][A-Za-z0-9-]{1,15}/g) ?? []
  const seen = new Set()
  return toks.filter((t) => {
    const k = t.toLowerCase()
    if (seen.has(k) || isForbiddenToken(t)) return false
    seen.add(k)
    return true
  }).slice(0, 8)
}

const decodeEntities = (s) => s.replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&quot;/g, '"').replace(/&amp;/g, '&')

// ---------------------------------------------------------------- 白名单读取（唯一权威源，只读旧树文件 ⛔不改）
function readWhitelist() {
  const src = readFileSync(GATEWAY, 'utf8')
  const start = src.indexOf('_PUBLIC_DOCS = {')
  if (start < 0) throw new Error('public_docs_ops.py: _PUBLIC_DOCS 未找到')
  const out = {}
  let i = start
  for (const fam of Object.keys(FAMILY_DIRS)) {
    const key = `"${fam}": (`
    const k = src.indexOf(key, i)
    if (k < 0) throw new Error(`public_docs_ops.py: 族 ${fam} 未找到`)
    let depth = 1
    let j = k + key.length
    while (depth > 0 && j < src.length) {
      const c = src[j]
      if (c === '(') depth++
      else if (c === ')') depth--
      j++
    }
    const block = src
      .slice(k + key.length, j - 1)
      .split('\n')
      .filter((l) => !l.trimStart().startsWith('#'))
      .join('\n')
    const items = [...block.matchAll(/"([^"\n]+)"/g)].map((m) => m[1])
    if (items.length === 0) throw new Error(`public_docs_ops.py: 族 ${fam} 清单为空`)
    out[fam] = items
    i = j
  }
  return out
}

// ---------------------------------------------------------------- 件头解析（md）
function mdTitle(head) {
  for (const line of head.split('\n')) {
    const t = line.trim()
    if (t.startsWith('# ')) {
      return decodeEntities(
        t.slice(2)
          .replace(/\*\*/g, '').replace(/`/g, '')
          .replace(/（[^（）]*(?:V\d[^（）]*)）/g, (m) => (m.includes('V') ? '' : m))
          .trim(),
      )
    }
  }
  return ''
}

function mdVersion(name, head) {
  const inName = name.match(/V\d+\.\d+(?:\.\d+)?(?:-[A-Za-z-]+)?/)
  if (inName) return inName[0]
  const inHead = head.slice(0, 800).match(/V\d+\.\d+(?:\.\d+)?(?:-[A-Za-z-]+)?/)
  return inHead ? inHead[0] : ''
}

function mdSummary(text) {
  const lines = text.split('\n')
  let seenTitle = false
  for (const raw of lines) {
    const t = raw.trim()
    if (!seenTitle) {
      if (t.startsWith('# ')) seenTitle = true
      continue
    }
    if (t === '' || t === '---' || t.startsWith('#') || t.startsWith('>') || t.startsWith('![') || t.startsWith('|')) continue
    const plain = decodeEntities(
      t.replace(/!\[[^\]]*\]\([^)]*\)/g, '')
        .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
        .replace(/^\s*[-*]\s+/, '')
        .replace(/[*`>]/g, '')
        .trim(),
    )
    if (plain.length === 0) continue
    return plain.length > 90 ? `${plain.slice(0, 90)}…` : plain
  }
  return ''
}

function mdNature(head, famKey) {
  const m = head.slice(0, 1500).match(/data_nature\s*[:：]\s*([a-z]+)/i)
  if (m) return m[1].toLowerCase()
  return famKey === 'cop-library' ? 'synthetic' : 'real'
}

function plainBody(text, limit) {
  const p = text
    .replace(/^---$/gm, ' ')
    .replace(/[#>*`|-]{1,}/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return p.length > limit ? p.slice(0, limit) : p
}

// ---------------------------------------------------------------- 件头解析（yaml·轻量）
function yamlScalar(block, key) {
  const m = block.match(new RegExp(`^\\s*${key}:\\s*(.+)$`, 'm'))
  return m ? m[1].trim().replace(/^'(.*)'$/, '$1').replace(/^"(.*)"$/, '$1') : ''
}

function yamlEntry(text, entry) {
  const base = entry.split('/').pop().replace(/-PUB\.yaml$/, '').replace(/\.yaml$/, '').replace(/\.md$/, '')
  const nature = (yamlScalar(text, 'data_nature') || (entry.endsWith('.md') ? '' : 'synthetic')).toLowerCase()
  let title = yamlScalar(text, 'display_name') || yamlScalar(text.slice(text.indexOf('soul:')), 'identity')
  if (!title || /[{}]/.test(title)) title = base
  let summary = yamlScalar(text.slice(text.indexOf('soul:')), 'core') || yamlScalar(text, 'source')
  if (!summary) summary = yamlScalar(text, 'branch') || base
  let version = (entry.match(/V\d+\.\d+(?:\.\d+)?(?:-[A-Za-z-]+)?/) ?? [''])[0]
  return { title: title.trim(), summary: summary.trim(), nature, version }
}

// ---------------------------------------------------------------- 术语快照解析（151 条）
function readTerms() {
  const src = readFileSync(TERMS_YAML, 'utf8')
  const exported = (src.match(/^exported_at:\s*(.+)$/m) ?? ['', ''])[1].trim()
  const entries = []
  let cur = null
  let inDef = false
  for (const raw of src.split('\n')) {
    if (raw.startsWith('- term: ')) {
      if (cur) entries.push(cur)
      cur = { term: raw.slice(8).trim(), def: '' }
      inDef = false
      continue
    }
    if (!cur) continue
    if (/^\s{2}def:\s*/.test(raw)) {
      cur.def = raw.replace(/^\s{2}def:\s*/, '').replace(/^'(.*)'$/, '$1').trim()
      inDef = true
      continue
    }
    if (inDef && /^\s{4,}\S/.test(raw)) {
      cur.def = `${cur.def} ${raw.trim()}`.replace(/\s+/g, ' ').trim()
      continue
    }
    inDef = false
  }
  if (cur) entries.push(cur)
  return { exported, entries }
}

// ---------------------------------------------------------------- 栏目页（本树 App.tsx 静态路由）
function readColumns() {
  const src = readFileSync(APP_TSX, 'utf8')
  const paths = [...src.matchAll(/<Route\s+path="([^"]+)"\s+element=\{/g)]
    .map((m) => m[1])
    .filter((p) => !p.includes(':') && p !== '*')
  const out = []
  const missing = []
  for (const p of paths) {
    if (COLUMN_EXCLUDE.has(p)) continue
    const title = COLUMN_TITLES[p]
    if (!title) {
      missing.push(p)
      continue
    }
    out.push({ path: p, title })
  }
  if (missing.length > 0) {
    throw new Error(`COLUMN_TITLES 缺题名路由 ${missing.length} 条：${missing.join(' ')}（fail-closed，须先补题名）`)
  }
  return out
}

// ---------------------------------------------------------------- 主流程
const whitelist = readWhitelist()
const { exported: termsExportedAt, entries: terms } = readTerms()
const columns = readColumns()

const entries = []
const missing = []
const exempted = []
let forbiddenStripped = 0
const stripLog = []

for (const [famKey, items] of Object.entries(whitelist)) {
  const dir = FAMILY_DIRS[famKey]
  const label = FAMILY_LABEL[famKey]
  for (const entry of items) {
    const diskName = resolveDiskName(famKey, entry)
    const file = join(DOCS, dir, diskName)
    if (!existsSync(file)) {
      if (EXEMPT_MISSING[`${famKey}/${entry}`]) {
        exempted.push(`${famKey}/${entry} :: ${EXEMPT_MISSING[`${famKey}/${entry}`]}`)
      } else {
        missing.push(`${famKey}/${entry}`)
      }
      continue
    }
    const text = readFileSync(file, 'utf8')
    // 题名源：制度族＝白名单在册公开名（NETNAME 逐件审定净名，唯一权威源）；
    // 其余族照旧版——md 取 H1 解析、yaml 取 display_name（禁则表共用，残留由零内部编号自校兜底）
    const pubName = entry.split('/').pop().replace(/\.(md|yaml)$/, '')
    let meta
    if (famKey === 'regulation') {
      const ym = entry.endsWith('.yaml') ? yamlEntry(text, entry) : null
      meta = {
        title: pubName,
        summary: ym ? ym.summary : mdSummary(text),
        nature: ym ? ym.nature : mdNature(text, famKey),
        version: mdVersion(entry, text.slice(0, 4000)),
      }
    } else if (entry.endsWith('.yaml')) {
      meta = yamlEntry(text, entry)
    } else {
      meta = {
        title: mdTitle(text.slice(0, 4000)) || pubName,
        summary: mdSummary(text),
        nature: mdNature(text, famKey),
        version: mdVersion(entry, text.slice(0, 4000)),
      }
    }
    const bodyRaw = plainBody(text, 1500)
    const before = `${meta.title}|${meta.summary}|${bodyRaw}`
    meta.title = stripForbidden(meta.title)
    meta.summary = stripForbidden(meta.summary)
    const bodyClean = stripForbidden(bodyRaw)
    if (before !== `${meta.title}|${meta.summary}|${bodyClean}`) {
      forbiddenStripped++
      stripLog.push(`${famKey}/${entry} :: ${before.slice(0, 90)}`)
    }
    entries.push({
      title: meta.title,
      family: label,
      summary: meta.summary,
      keywords: latinTokens(`${meta.title} ${entry.split('/').pop()}`),
      url: `/docs/${famKey}/${entry}`,
      slug: slugFromEntry(entry),
      version: meta.version,
      nature: meta.nature,
      body: bodyClean,
    })
  }
}

for (const t of terms) {
  const def = stripForbidden(t.def.replace(/〔内部编号〕/g, '（内部编号已脱敏）'))
  entries.push({
    title: stripForbidden(t.term),
    family: '术语',
    summary: def.length > 90 ? `${def.slice(0, 90)}…` : def,
    keywords: latinTokens(t.term),
    url: '/terms',
    version: '',
    nature: 'real',
    body: def.length > 300 ? def.slice(0, 300) : def,
  })
}

for (const c of columns) {
  entries.push({
    title: stripForbidden(c.title),
    family: '栏目',
    summary: '',
    keywords: latinTokens(c.title),
    url: c.path,
    version: '',
    nature: 'real',
    body: '',
  })
}

if (missing.length > 0) {
  console.error(`✗ 白名单件在磁盘缺失 ${missing.length} 件（非豁免）：\n  ${missing.join('\n  ')}`)
  process.exit(1)
}
if (terms.length !== 151) {
  console.error(`✗ 术语快照解析得 ${terms.length} 条，应为 151`)
  process.exit(1)
}

// 硬约束第8条自校：产物全文（title/summary/body）零内部编号，命中即失败（fail-closed）
const INTERNAL_RESIDUAL = /\b(TDCA-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}|PUB-CORPUS-\d+|GSEQ-\d+|COP-\d+)\b/
const residual = entries.filter((e) =>
  INTERNAL_RESIDUAL.test(`${e.title} ${e.summary} ${e.body}`))
if (residual.length > 0) {
  console.error(`✗ 零内部编号自校失败：${residual.length} 条残留`)
  for (const e of residual.slice(0, 10)) console.error(`    [${e.family}] ${e.title.slice(0, 60)}`)
  process.exit(1)
}

const counts = {}
for (const f of FAMILY_ORDER) counts[f] = entries.filter((e) => e.family === f).length

const doc = {
  spec: 'TDCA-SEARCH-INDEX-V1',
  generated_at: new Date().toISOString(),
  generated_by: 'tdca-site scripts/build-search-index.mjs（构建时静态生成）',
  sources: {
    public_docs: 'gateway/public_docs_ops.py 在册公开清单（唯一权威源，只读）',
    terms: `docs/terms 术语快照（151 条，exported_at ${termsExportedAt}）`,
    columns: 'tdca-site App.tsx 静态路由 ∩ COLUMN_TITLES 题名录（动作页/检索页除外）',
  },
  counts,
  total: entries.length,
  missing_exempt: exempted.map((s) => s.split(' :: ')[0]),
  entries,
}

mkdirSync(OUT_DIR, { recursive: true })
writeFileSync(OUT, `${JSON.stringify(doc)}\n`, 'utf8')
console.log(`✓ public/search-index.json 生成：共 ${entries.length} 条`)
for (const f of FAMILY_ORDER) console.log(`  ${f}: ${counts[f]}`)
console.log(`  栏目页来源: ${columns.length} 项静态路由`)
if (exempted.length > 0) {
  console.log(`  ⚠ 豁免缺件 ${exempted.length} 件（白名单在册而仓内无源，已挂账候裁）：`)
  for (const s of exempted) console.log(`    ${s}`)
}
if (forbiddenStripped > 0) console.log(`  ⚠ 编号形态剥除: ${forbiddenStripped} 处（title/summary 命中禁则已剥除）`)
for (const s of stripLog) console.log(`    ${s}`)
console.log('  ✓ 零内部编号自校通过')
