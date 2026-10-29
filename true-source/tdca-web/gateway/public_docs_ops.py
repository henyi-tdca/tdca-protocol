# -*- coding: utf-8 -*-
"""
公开只读制度件取得面（丙案 · L1SI151-PUBLIC-ROUTE-001）。

口径（入站判据 P-1~P-5之前置 · TDCA-RULING-SITE-INGEST-DEFINITION-001）：
  - 入站＝公网可取得件：本面即「可发现（P-1）＋可取得（P-2）」之公开承载面；
  - 匿名只读：仅 GET；写方法一律不开放（未定义即 405 fail-closed）；
  - 只列已入站公开件：以在册公开清单为准（regulation 17 · whitepapers 2 · papers 13 · L1SI154-010 扩面），
    ⛔ 未入站件不出现、⛔ 乙类存证件永不出现（fail-closed：越界取件 404，
    ⛔ 不借 404/200 之差泄露在仓与否之外的信息——统一 404）；
  - 单一事实源：件即容器内只读文件（docs/regulations/），sha256 由文件现算，
    ⛔ 不另建库表副本、⛔ 不双源各算；
  - 不带私域：⛔ 内部编号（件内若残留编号属内容本身，照实返回——入站核验另扫）、
    ⛔ 运维字段、⛔ 他人数据、⛔ 计量与额度；
  - 限流：60 次/分/IP（滑动窗口，防枚举）；
  - 别名：旧 /api/site/docs/* 指向同一实现（⛔ 不双实现），仅为前端不改。
SPDX-License-Identifier: TDCA-Internal
"""
from __future__ import annotations

import hashlib
import os
import re
import threading
import time
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from error_codes import with_code  # L1SI153 段一：拒绝体仅增设 code 字段

router = APIRouter(prefix="/api/public", tags=["public-docs"])
# 别名路由：与主路由同一实现（同一处理函数），仅为前端不改（施工令 §二）
alias_router = APIRouter(prefix="/api/site", tags=["public-docs-alias"])

# ---------------------------------------------------------------------
# 在册公开清单（regulation 49／whitepapers 2／papers 13 · L1SI154-010 扩面 + L1SI154-028 九件 + L1SI155-INGEST-002 十六件 + L1SI164-NCA 三件 + L1SI180-TERMS-004/005 三件 + L1SI181-REG-NODE-ACCESS-PUB-001 节点条例两件）
# 原「乙类 2 件（签批记录／生效注记）不得列入」经 L1SI180-TERMS-001 入站批 2 改写零命中、TERMS-004 放行、TERMS-005 甲案（创始人逐字）解除；
# 更新本清单须另有在册依据（入站批次放行件），⛔ 不得随代码静默扩面。
# ---------------------------------------------------------------------
_FAMILY = "regulation"  # 默认族：裸 /api/public/docs 兼容行为（仍列 regulation）
# L1SI154-010：多族承载——族 → 容器内目录（/docs/<dir>，只读挂载）
_FAMILY_DIRS = {"regulation": "regulations", "whitepapers": "whitepapers", "papers": "papers", "cop-library": "cop-library"}
_PUBLIC_DOCS = {
    "regulation": (
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（单一权威稿·中文人读版V1.0-FROZEN）.md",
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（英文人读版V1.0-FROZEN）.md",
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（机读版V1.0-FROZEN）.yaml",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（中文人读版V1.0-FROZEN）.md",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（英文人读版V1.0-FROZEN）.md",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（机读版V1.0-FROZEN）.yaml",
    "TDCA-PUB-CORPUS-059-场景线相遇专章对外版单独件（V1.0已生效·十七条·供站上替换旧草案版）.md",
    "TDCA-PUB-CORPUS-017-可信协作宪法（对外可读版·V0.1草案候选·十条与序言四支柱）.md",
    "TDCA-PUB-CORPUS-043-Constitution-EN-可信协作宪法英文人读版（V0.1·十条与四支柱·逐条对应中文）.md",
    "TDCA-PUB-CORPUS-044-Constitution-MACHINE-可信协作宪法机读版（V0.1·十条与四支柱·与中文英文互见）.yaml",
    "TDCA-PUB-CORPUS-029-卷二纯版第二批清理版重出-身份可信等级认定条例对外版（仅去符号·语义同028·六检通过）.md",
    "TDCA-PUB-CORPUS-045-IdentityTier-EN-身份可信等级认定条例英文人读版（十六条·V1.0·逐条对应中文）.md",
    "TDCA-PUB-CORPUS-046-IdentityTier-MACHINE-身份可信等级认定条例机读版（四档与判定次序与三态·V1.0·互见）.yaml",
    "TDCA-PUB-CORPUS-030-卷二纯版第三批-智能体定义条例对外版（二十一条·V1.0已生效·六检通过·引用不重写）.md",
    "TDCA-PUB-CORPUS-047-AgentDefinition-EN-智能体定义条例英文人读版（二十一条·V1.0·逐条对应中文）.md",
    "TDCA-PUB-CORPUS-048-AgentDefinition-MACHINE-智能体定义条例机读版（本体与创世与主体与效用与生命周期·V1.0互见）.yaml",
    "TDCA-PUB-CORPUS-083-流程环节卡发现（五问·六类失败·第4张卡）.md",
    "TDCA-PUB-CORPUS-084-流程环节卡相遇（五问·六类失败·第5张卡）.md",
    "TDCA-PUB-CORPUS-085-流程环节卡握手（五问·七类失败·第6张卡）.md",
    "TDCA-PUB-CORPUS-086-流程环节卡签约（五问·七类失败·第7张卡）.md",
    "TDCA-PUB-CORPUS-087-流程环节卡交付（五问·七类失败·第8张卡）.md",
    "TDCA-PUB-CORPUS-088-流程环节卡验收（五问·七类失败·第9张卡）.md",
    "TDCA-PUB-CORPUS-090-卷四治理卷对外版（谁定规则与怎么改与怎么监督与争议边界·首件）.md",
    "TDCA-PUB-CORPUS-091-卷五同构卷对外版（制度与技术同构与本体同构与场景嵌套·移植四步·边界四条）.md",
    "TDCA-PUB-CORPUS-092-卷六助手与入口对外版（三类入口与助手四步接入与代签红线）.md",
    # L1SI155-INGEST-002：十五件入册（A 三已生效条例 ＋ B 治理规范 ＋ E 卷三卡十一）＋ AMEND-1 授权件模板对外版（第 16 件）
    "TDCA-PUB-CORPUS-069-惩罚三态与守门器对外纯版（二十五条与AB九条·V1.0已生效2026-10-16）.md",
    "TDCA-PUB-CORPUS-070-租户与环境作用域凭证绑定条例对外纯版（三规则一通路一分层·V1.0已生效2026-09-25）.md",
    "TDCA-PUB-CORPUS-071-IP版权资产评估管理办法对外纯版（三十一条齐·V1.0已生效2026-09-30）.md",
    "TDCA-PUB-CORPUS-074-制度治理规范对外纯版（六判据链·英文待补）.md",
    "TDCA-PUB-CORPUS-058-流程环节卡注册缔约（五问·七类失败·三句固定·第三张卡）.md",
    "TDCA-PUB-CORPUS-101-流程环节卡授权配置（五问·七类失败·第1张卡补五问版）.md",
    "TDCA-PUB-CORPUS-102-流程环节卡结算计税（五问·七类失败·第2张卡补五问版）.md",
    "TDCA-PUB-CORPUS-097-流程环节卡谈判（五问·七类失败·第10张卡）.md",
    "TDCA-PUB-CORPUS-098-流程环节卡试错（五问·七类失败·第11张卡）.md",
    "TDCA-PUB-CORPUS-099-流程环节卡验证（五问·七类失败·第12张卡）.md",
    "TDCA-PUB-CORPUS-100-流程环节卡履约准备（五问·七类失败·第13张卡）.md",
    "TDCA-PUB-CORPUS-093-流程环节卡履约（五问·七类失败·第14张卡）.md",
    "TDCA-PUB-CORPUS-094-流程环节卡结算分配（五问·七类失败·第15张卡）.md",
    "TDCA-PUB-CORPUS-095-流程环节卡信用及遗产管理（五问·七类失败·第16张卡）.md",
    "TDCA-PUB-CORPUS-096-流程环节卡争议裁决（五问·七类失败·第17张卡）.md",
    "TDCA-PUB-CORPUS-103-授权件模板对外版（中文人读·V1.0-FROZEN按签批更正版本面貌·八字段与四要件）.md",
    # L1SI164-NCA-EXT-INSITE-001（AMEND-2 授权追加）：存证（NCA）制度对外节选版 R2 件——regulation 42→43
    "TDCA-PUB-NCA-STD-001-EXT-V1.1-存证（NCA）制度对外节选版（已生效·与内部V1.1同版·差异清单）-R2.md",
    # L1SI164-NCA-GENESIS-REG-INSITE-001（授权追加）：官方可信认知资产登记件（对外节选版）——regulation 43→44
    "TDCA-PUB-NCA-GENESIS-REG-001-TDCA官方可信认知资产登记·创世认知资产区块（人读·已登记·对外节选版）.md",
    # L1SI164-NCA-GENESIS-REG-INSITE-001-AMEND-1（授权追加）：创世区块完整证据件（对外版）——regulation 44→45
    "TDCA-PUB-NCA-GENESIS-EVID-001-官方可信认知资产·创世区块完整证据（三块·算法·签批·自验）-对外版.md",
    # L1SI180-TERMS-004/005 甲案（创始人逐字「一并上·授权重启」）：入站批 2 三件上站（复扫零命中·磁盘已与树逐字节符）——regulation 44→47
    "TDCA-SIGNOFF-CONFIGMARKET-AUTH-001-追认附记.md",
    "TDCA-SIGNOFF-SCENE-ENCOUNTER-001-场景线·相遇专章·签批记录（条例·创始人签批·V1.0生效）.md",
    "TDCA-TEMPLATE-AUTH-001-生效注记.md",
    # L1SI181-REG-NODE-ACCESS-PUB-001（创始人逐字「节点条例可以入仓对外公开入站」；条文一字不改）：
    # 《业务端节点接入与同构契约条例》对外公开版 人读＋机读两件入册——regulation 47→49
    "TDCA-REG-NODE-ACCESS-001（对外公开版·V1.0）.md",
    "TDCA-REG-NODE-ACCESS-001-COMPILED（对外公开版·V1.0）.yaml",
    ),
    # L1SI154-010：白皮书 2 件全量（已全量扫六类内部编号零命中）
    "whitepapers": (
    "TDCA-AI-GOVERNANCE-WP-001.md",
    "TDCA-COG-WP-001.md",
    ),
    # L1SI154-010：论文顶层正文 13 件（README/.gitattributes 元数据件不入；evidence/ 默认排除）
    "papers": (
    "TDCA-FUNCTION-WP-002-APPX-G-附录G-制度大模型与制度孪生函数化登记.md",
    "TDCA-FUNCTION-WP-002-函数白皮书.md",
    "TDCA-MATH-WP-REV-001-数学基础白皮书修订本.md",
    "TDCA-MONOGRAPH-COP-001.md",
    "TDCA-MONOGRAPH-IT-001.md",
    "TDCA-PAPER-ENGINEERING-PHILOSOPHY-001-工程哲学-English-V1.0.md",
    "TDCA-PAPER-ENGINEERING-PHILOSOPHY-001-工程哲学-中文版-V1.0.md",
    "TDCA-PAPER-FUNCTIONAL-LM-001.md",
    "TDCA-PAPER-PHILOSOPHY-001-制度哲学-English-V1.0.md",
    "TDCA-PAPER-PHILOSOPHY-001-制度哲学-中文版-V1.0.md",
    "TDCA-WP-MATERIALISM-001.md",
    "TDCA-paper-CN.md",
    "TDCA-paper-EN.md",
    ),
    # L1SI170-COPLIB-001/002/005：cop-library 族 56 件（只 md·白名单制·⛔整目录）
    # 首批 31 件（COPLIB-001，01/02/03 系 A2 新版）＋ 批 2 之 25 件（COPLIB-005 判定表未标「不放」者）
    # ⛔ 放六件（内部编号，待改另批）：simulations/README、MCP-LIVE-TEST-REPORT、
    #    REAL-SUNZI-3PHASE×2、REAL-SUNZI-COLLAB、SUNZI-COLLAB-REPORT
    "cop-library": (
    "README.md",
    "OPENING.md",
    # L1SI180-TERMS-004/005 甲案上站一件（入站批 2 · 未入册⟹幂等补入 · 磁盘已与 main 树逐字节符）
    "OPENING-LEDGER-L1SI177.md",
    "COP-MANIFEST-2026-09-13.md",
    "tdca_core/README.md",
    "simulations/multilateral_search_match/README.md",
    "engineering-three/01-试验思维协议.md",
    "engineering-three/02-灰度管理思维协议.md",
    "engineering-three/03-可靠性设计思维协议.md",
    "engineering-three/04-智能体安全管理化合协议.md",
    "engineering-three/05-工程三×场景×TDCA-双层化合协议.md",
    "hundred_schools/README.md",
    "hundred_schools/COMPOSITION-REPORT-道德经_可审计决策.md",
    "hundred_schools/daodejing/COMPOSITION-REPORT-第36章_可审计决策.md",
    "hundred_schools/daxue/COMPOSITION-REPORT-第03目_可审计决策.md",
    "hundred_schools/lunyu/COMPOSITION-REPORT-第12篇_可审计决策.md",
    "hundred_schools/sunzi/sunzi_real/计篇_战略蒸馏.md",
    "hundred_schools/sunzi/sunzi_real/计篇_训诂校勘.md",
    "compositions/COMPOSITION-REPORT.md",
    "compositions/COMPOSITION-REPORT-囚徒困境_最后通牒博弈.md",
    "compositions/COMPOSITION-REPORT-囚徒困境_机制设计.md",
    "compositions/COMPOSITION-REPORT-囚徒困境_认知涌现.md",
    "compositions/COMPOSITION-REPORT-围魏救赵_囚徒困境.md",
    "compositions/COMPOSITION-REPORT-围魏救赵_斗鸡博弈.md",
    "compositions/COMPOSITION-REPORT-场景思维协议_囚徒困境.md",
    "compositions/COMPOSITION-REPORT-场景画布_囚徒困境.md",
    "compositions/COMPOSITION-REPORT-数据治理_机制设计.md",
    "compositions/COMPOSITION-REPORT-机制设计_场景思维协议.md",
    "compositions/COMPOSITION-REPORT-生命周期适配_走为上.md",
    "compositions/COMPOSITION-REPORT-走为上_囚徒困境.md",
    "compositions/COMPOSITION-REPORT-走为上_猎鹿博弈.md",
    # 批 2（25 件，COPLIB-005）
    "simulations/multilateral_search_match/MCP-LIVE-AB-UTILITY-REPORT.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-LOCAL8.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-MCP-A.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-MCP-AB.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-MCP-B.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-MCP-BASE.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-MCP-FALLBACK.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-MCP-LIVE.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-MCP-LIVE-SW.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-MCP-NAMED.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-REAL-A.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-REAL-BASE.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-REAL-SINGLE.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-REAL-SINGLE-BASE.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-RESULT.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-SCALE200.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-SCALE200-MC.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-SCALE600.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-V2.md",
    "simulations/multilateral_search_match/SEARCH-MATCH-V3.md",
    "simulations/positivesum_negotiation/POSITIVE-SUM-RESULT.md",
    "simulations/positivesum_negotiation/SIMULATION-TRACE.md",
    "simulations/zou_wei_shang_transformation/BUSINESS-TRANSFORMATION-PLAN.md",
    "simulations/zou_wei_shang_transformation/SIMULATION-TRACE.md",
    # 六件去编号改写后放行（L1SI170-COPLIB-008，承 007 硬排除解除）
    "simulations/README.md",
    "simulations/multilateral_search_match/MCP-LIVE-TEST-REPORT.md",
    "simulations/multilateral_search_match/REAL-SUNZI-3PHASE-REPORT.md",
    "simulations/multilateral_search_match/REAL-SUNZI-3PHASE-REPORT-HONEST.md",
    "simulations/multilateral_search_match/REAL-SUNZI-COLLAB-REPORT.md",
    "simulations/multilateral_search_match/SUNZI-COLLAB-REPORT.md",
    # 批 L1SI177-B123-RECOMMEND 块乙：素材库双版试点 14 件——只列「-PUB」对外版
    # （原件带 COP-ID/base_protocol 注册号不入册；对外版已剥件首元数据头＋补 data_nature+来源句）
    # 收口（L1SI177-B4-FOLLOWUP 块乙）：缓办两件撤条——emissary/谈判者-特使-001-COP-PUB、麦肯锡思维协议-PUB
    # 正文残余注册号（特使 dispatch 图谱 SCEN-COP×7／麦肯锡基协议号×1）已中性化改写，⛔ 未删文件，
    # 留仓待智库核过改写件后另令入站；现网白名单 74→72。
    # TAIL-CLEAN-001 块C（2026-10-28）：另令已至，两件回收入站——字节实测 3839/2993 与令面相符、
    # 禁区复扫零命中（承智库核）；本批 72→74、全族 287→289。⛔ 不动既有条、⛔ 不动台账；现网待部署。
    "mechanism_design/第01机制-机制设计-PUB.yaml",
    "games/第01博弈-囚徒困境-PUB.yaml",
    "games/第02博弈-猎鹿博弈-PUB.yaml",
    "games/第03博弈-斗鸡博弈-PUB.yaml",
    "games/第04博弈-最后通牒博弈-PUB.yaml",
    "scenario/第01场景-场景思维协议-PUB.yaml",
    "scenario/第02场景-场景画布-PUB.yaml",
    "scenario/第03场景-认知涌现-PUB.yaml",
    "scenario/第04场景-嵌套法则-PUB.yaml",
    "scenario/第05场景-生命周期适配-PUB.yaml",
    "scenario/第06场景-数据治理-PUB.yaml",
    "scenario/第07场景-认知模型衔接-PUB.yaml",
    "emissary/谈判者-特使-001-COP-PUB.yaml",
    "麦肯锡思维协议-PUB.yaml",
    # 批 L1SI177-COPLIB-BCBATCH-001 双版令——只列「-PUB」对外版（原件不入册；停手 1 件见台账）
    # 批 B（65 件）：剥注册号头＋补 data_nature/来源句
    "microeconomics/第01条-供给与需求·均衡-PUB.yaml",
    "microeconomics/第02条-需求弹性-PUB.yaml",
    "microeconomics/第03条-消费者选择·效用最大化-PUB.yaml",
    "microeconomics/第04条-收入与替代效应-PUB.yaml",
    "microeconomics/第05条-生产者理论·成本-PUB.yaml",
    "microeconomics/第06条-完全竞争-PUB.yaml",
    "microeconomics/第07条-垄断-PUB.yaml",
    "microeconomics/第08条-寡头·策略互动-PUB.yaml",
    "microeconomics/第09条-垄断竞争-PUB.yaml",
    "microeconomics/第10条-一般均衡与福利-PUB.yaml",
    "microeconomics/第11条-外部性·科斯-PUB.yaml",
    "microeconomics/第12条-公共品与信息不对称-PUB.yaml",
    "marxism/第01条-物质第一性-PUB.yaml",
    "marxism/第02条-对立统一规律-PUB.yaml",
    "marxism/第03条-质量互变规律-PUB.yaml",
    "marxism/第04条-否定之否定-PUB.yaml",
    "marxism/第05条-普遍联系-PUB.yaml",
    "marxism/第06条-永恒发展-PUB.yaml",
    "marxism/第07条-矛盾普遍性-PUB.yaml",
    "marxism/第08条-矛盾特殊性-PUB.yaml",
    "marxism/第09条-主要矛盾与矛盾主要方面-PUB.yaml",
    "marxism/第10条-同一性与斗争性-PUB.yaml",
    "marxism/第11条-对抗在矛盾中的地位-PUB.yaml",
    "marxism/第12条-实践第一-PUB.yaml",
    "marxism/第13条-认识辩证运动-PUB.yaml",
    "marxism/第14条-实事求是-PUB.yaml",
    "marxism/第15条-真理相对绝对-PUB.yaml",
    "stratagems/第01计-瞒天过海-PUB.yaml",
    "stratagems/第02计-围魏救赵-PUB.yaml",
    "stratagems/第03计-借刀杀人-PUB.yaml",
    "stratagems/第04计-以逸待劳-PUB.yaml",
    "stratagems/第05计-趁火打劫-PUB.yaml",
    "stratagems/第06计-声东击西-PUB.yaml",
    "stratagems/第07计-无中生有-PUB.yaml",
    "stratagems/第08计-暗度陈仓-PUB.yaml",
    "stratagems/第09计-隔岸观火-PUB.yaml",
    "stratagems/第10计-笑里藏刀-PUB.yaml",
    "stratagems/第11计-李代桃僵-PUB.yaml",
    "stratagems/第12计-顺手牵羊-PUB.yaml",
    "stratagems/第13计-打草惊蛇-PUB.yaml",
    "stratagems/第14计-借尸还魂-PUB.yaml",
    "stratagems/第15计-调虎离山-PUB.yaml",
    "stratagems/第16计-欲擒故纵-PUB.yaml",
    "stratagems/第17计-抛砖引玉-PUB.yaml",
    "stratagems/第18计-擒贼擒王-PUB.yaml",
    "stratagems/第19计-釜底抽薪-PUB.yaml",
    "stratagems/第20计-浑水摸鱼-PUB.yaml",
    "stratagems/第21计-金蝉脱壳-PUB.yaml",
    "stratagems/第22计-关门捉贼-PUB.yaml",
    "stratagems/第23计-远交近攻-PUB.yaml",
    "stratagems/第24计-假道伐虢-PUB.yaml",
    "stratagems/第25计-偷梁换柱-PUB.yaml",
    "stratagems/第26计-指桑骂槐-PUB.yaml",
    "stratagems/第27计-假痴不癫-PUB.yaml",
    "stratagems/第28计-上屋抽梯-PUB.yaml",
    "stratagems/第29计-树上开花-PUB.yaml",
    "stratagems/第30计-反客为主-PUB.yaml",
    "stratagems/第31计-美人计-PUB.yaml",
    "stratagems/第32计-空城计-PUB.yaml",
    "stratagems/第33计-反间计-PUB.yaml",
    "stratagems/第34计-苦肉计-PUB.yaml",
    "stratagems/第35计-连环计-PUB.yaml",
    "stratagems/第36计-走为上-PUB.yaml",
    "stratagems/bindings/打草惊蛇-场景A-侦查试探-PUB.yaml",
    "stratagems/bindings/打草惊蛇-场景B-暴露警示-PUB.yaml",
    # 批 C（150 件）：剥注册号头＋补 data_nature/来源句
    "chengyu/第01条-完璧归赵-PUB.yaml",
    "chengyu/第02条-负荆请罪-PUB.yaml",
    "chengyu/第03条-纸上谈兵-PUB.yaml",
    "chengyu/第04条-卧薪尝胆-PUB.yaml",
    "chengyu/第05条-草木皆兵-PUB.yaml",
    "chengyu/第06条-破釜沉舟-PUB.yaml",
    "chengyu/第07条-暗度陈仓-PUB.yaml",
    "chengyu/第08条-退避三舍-PUB.yaml",
    "chengyu/第09条-一鸣惊人-PUB.yaml",
    "chengyu/第10条-唇亡齿寒-PUB.yaml",
    "chengyu/第11条-塞翁失马-PUB.yaml",
    "chengyu/第12条-守株待兔-PUB.yaml",
    "chengyu/第13条-刻舟求剑-PUB.yaml",
    "chengyu/第14条-掩耳盗铃-PUB.yaml",
    "chengyu/第15条-画蛇添足-PUB.yaml",
    "chengyu/第16条-盲人摸象-PUB.yaml",
    "chengyu/第17条-杯弓蛇影-PUB.yaml",
    "chengyu/第18条-庖丁解牛-PUB.yaml",
    "chengyu/第19条-邯郸学步-PUB.yaml",
    "chengyu/第20条-井底之蛙-PUB.yaml",
    "chengyu/第21条-一诺千金-PUB.yaml",
    "chengyu/第22条-滥竽充数-PUB.yaml",
    "chengyu/第23条-愚公移山-PUB.yaml",
    "chengyu/第24条-精卫填海-PUB.yaml",
    "chengyu/第25条-闻鸡起舞-PUB.yaml",
    "chengyu/第26条-三顾茅庐-PUB.yaml",
    "chengyu/第27条-萧规曹随-PUB.yaml",
    "chengyu/第28条-指鹿为马-PUB.yaml",
    "chengyu/第29条-朝三暮四-PUB.yaml",
    "chengyu/第30条-防微杜渐-PUB.yaml",
    "chengyu/第31条-田忌赛马-PUB.yaml",
    "chengyu/第32条-鹬蚌相争-PUB.yaml",
    "chengyu/第33条-合纵连横-PUB.yaml",
    "chengyu/第34条-远交近攻-PUB.yaml",
    "chengyu/第35条-假道伐虢-PUB.yaml",
    "chengyu/第36条-围魏救赵-PUB.yaml",
    "chengyu/第37条-杯酒释兵权-PUB.yaml",
    "chengyu/第38条-徙木立信-PUB.yaml",
    "chengyu/第39条-纲举目张-PUB.yaml",
    "chengyu/第40条-居安思危-PUB.yaml",
    "chengyu/第41条-知己知彼-PUB.yaml",
    "chengyu/第42条-物极必反-PUB.yaml",
    "chengyu/第43条-相反相成-PUB.yaml",
    "chengyu/第44条-否极泰来-PUB.yaml",
    "chengyu/第45条-举一反三-PUB.yaml",
    "chengyu/第46条-格物致知-PUB.yaml",
    "chengyu/第47条-买椟还珠-PUB.yaml",
    "chengyu/第48条-奇货可居-PUB.yaml",
    "chengyu/第49条-因地制宜-PUB.yaml",
    "chengyu/第50条-开源节流-PUB.yaml",
    "chengyu/第51条-量入为出-PUB.yaml",
    "chengyu/第52条-集思广益-PUB.yaml",
    "chengyu/第53条-三思而行-PUB.yaml",
    "chengyu/第54条-曲突徙薪-PUB.yaml",
    "chengyu/第55条-叶公好龙-PUB.yaml",
    "chengyu/第56条-自相矛盾-PUB.yaml",
    "chengyu/第57条-画龙点睛-PUB.yaml",
    "chengyu/第58条-对症下药-PUB.yaml",
    "chengyu/第59条-釜底抽薪-PUB.yaml",
    "chengyu/第60条-水能载舟-PUB.yaml",
    "chengyu/2026-08-28/第61条-背水一战-PUB.yaml",
    "chengyu/2026-08-28/第62条-四面楚歌-PUB.yaml",
    "chengyu/2026-08-28/第63条-一鼓作气-PUB.yaml",
    "chengyu/2026-08-28/第64条-兵贵神速-PUB.yaml",
    "chengyu/2026-08-28/第65条-运筹帷幄-PUB.yaml",
    "chengyu/2026-08-28/第66条-螳螂捕蝉-PUB.yaml",
    "chengyu/2026-08-28/第67条-哀兵必胜-PUB.yaml",
    "chengyu/2026-08-28/第68条-攻心为上-PUB.yaml",
    "chengyu/2026-08-28/第69条-打草惊蛇-PUB.yaml",
    "chengyu/2026-08-28/第70条-先发制人-PUB.yaml",
    "chengyu/2026-08-28/第71条-亡羊补牢-PUB.yaml",
    "chengyu/2026-08-28/第72条-拔苗助长-PUB.yaml",
    "chengyu/2026-08-28/第73条-缘木求鱼-PUB.yaml",
    "chengyu/2026-08-28/第74条-对牛弹琴-PUB.yaml",
    "chengyu/2026-08-28/第75条-东施效颦-PUB.yaml",
    "chengyu/2026-08-28/第76条-疑邻盗斧-PUB.yaml",
    "chengyu/2026-08-28/第77条-郑人买履-PUB.yaml",
    "chengyu/2026-08-28/第78条-抱薪救火-PUB.yaml",
    "chengyu/2026-08-28/第79条-南辕北辙-PUB.yaml",
    "chengyu/2026-08-28/第80条-夜郎自大-PUB.yaml",
    "chengyu/2026-08-28/第81条-望梅止渴-PUB.yaml",
    "chengyu/2026-08-28/第82条-论功行赏-PUB.yaml",
    "chengyu/2026-08-28/第83条-任人唯贤-PUB.yaml",
    "chengyu/2026-08-28/第84条-兼听则明-PUB.yaml",
    "chengyu/2026-08-28/第85条-约法三章-PUB.yaml",
    "chengyu/2026-08-28/第86条-休养生息-PUB.yaml",
    "chengyu/2026-08-28/第87条-水滴石穿-PUB.yaml",
    "chengyu/2026-08-28/第88条-惩前毖后-PUB.yaml",
    "chengyu/2026-08-28/第89条-三省吾身-PUB.yaml",
    "chengyu/2026-08-28/第90条-竭泽而渔-PUB.yaml",
    "chengyu/2026-08-28/第91条-金蝉脱壳-PUB.yaml",
    "chengyu/2026-08-28/第92条-欲擒故纵-PUB.yaml",
    "chengyu/2026-08-28/第93条-调虎离山-PUB.yaml",
    "chengyu/2026-08-28/第94条-借刀杀人-PUB.yaml",
    "chengyu/2026-08-28/第95条-空城计-PUB.yaml",
    "chengyu/2026-08-28/第96条-苦肉计-PUB.yaml",
    "chengyu/2026-08-28/第97条-连环计-PUB.yaml",
    "chengyu/2026-08-28/第98条-擒贼擒王-PUB.yaml",
    "chengyu/2026-08-28/第99条-李代桃僵-PUB.yaml",
    "chengyu/2026-08-28/第100条-假痴不癫-PUB.yaml",
    "chengyu/2026-08-28/第101条-管中窥豹-PUB.yaml",
    "chengyu/2026-08-28/第102条-温故知新-PUB.yaml",
    "chengyu/2026-08-28/第103条-循序渐进-PUB.yaml",
    "chengyu/2026-08-28/第104条-因势利导-PUB.yaml",
    "chengyu/2026-08-28/第105条-触类旁通-PUB.yaml",
    "chengyu/2026-08-28/第106条-舍本逐末-PUB.yaml",
    "chengyu/2026-08-28/第107条-饮鸩止渴-PUB.yaml",
    "chengyu/2026-08-28/第108条-杯水车薪-PUB.yaml",
    "chengyu/2026-08-28/第109条-削足适履-PUB.yaml",
    "chengyu/2026-08-28/第110条-讳疾忌医-PUB.yaml",
    "chengyu/2026-08-28/第111条-赏罚分明-PUB.yaml",
    "chengyu/2026-08-28/第112条-集腋成裘-PUB.yaml",
    "chengyu/2026-08-28/第113条-广开言路-PUB.yaml",
    "chengyu/2026-08-28/第114条-有备无患-PUB.yaml",
    "chengyu/2026-08-28/第115条-正本清源-PUB.yaml",
    "chengyu/2026-08-28/第116条-从善如流-PUB.yaml",
    "chengyu/2026-08-28/第117条-精兵简政-PUB.yaml",
    "chengyu/2026-08-28/第118条-令行禁止-PUB.yaml",
    "chengyu/2026-08-28/第119条-过犹不及-PUB.yaml",
    "chengyu/2026-08-28/第120条-解铃系铃-PUB.yaml",
    "chengyu/2026-08-28/第121条-上屋抽梯-PUB.yaml",
    "chengyu/2026-08-28/第122条-关门捉贼-PUB.yaml",
    "chengyu/2026-08-28/第123条-偷梁换柱-PUB.yaml",
    "chengyu/2026-08-28/第124条-指桑骂槐-PUB.yaml",
    "chengyu/2026-08-28/第125条-反客为主-PUB.yaml",
    "chengyu/2026-08-28/第126条-树上开花-PUB.yaml",
    "chengyu/2026-08-28/第127条-以逸待劳-PUB.yaml",
    "chengyu/2026-08-28/第128条-隔岸观火-PUB.yaml",
    "chengyu/2026-08-28/第129条-走为上-PUB.yaml",
    "chengyu/2026-08-28/第130条-反间计-PUB.yaml",
    "chengyu/2026-08-28/第131条-一叶障目-PUB.yaml",
    "chengyu/2026-08-28/第132条-积羽沉舟-PUB.yaml",
    "chengyu/2026-08-28/第133条-见微知著-PUB.yaml",
    "chengyu/2026-08-28/第134条-数往知来-PUB.yaml",
    "chengyu/2026-08-28/第135条-画虎类犬-PUB.yaml",
    "chengyu/2026-08-28/第136条-胶柱鼓瑟-PUB.yaml",
    "chengyu/2026-08-28/第137条-抱残守缺-PUB.yaml",
    "chengyu/2026-08-28/第138条-审时度势-PUB.yaml",
    "chengyu/2026-08-28/第139条-权衡轻重-PUB.yaml",
    "chengyu/2026-08-28/第140条-推陈出新-PUB.yaml",
    "chengyu/2026-08-28/第141条-循名责实-PUB.yaml",
    "chengyu/2026-08-28/第142条-各得其所-PUB.yaml",
    "chengyu/2026-08-28/第143条-量才录用-PUB.yaml",
    "chengyu/2026-08-28/第144条-举直错枉-PUB.yaml",
    "chengyu/2026-08-28/第145条-张弛有度-PUB.yaml",
    "chengyu/2026-08-28/第146条-群策群力-PUB.yaml",
    "chengyu/2026-08-28/第147条-同舟共济-PUB.yaml",
    "chengyu/2026-08-28/第148条-约定俗成-PUB.yaml",
    "chengyu/2026-08-28/第149条-移风易俗-PUB.yaml",
    "chengyu/2026-08-28/第150条-有教无类-PUB.yaml",
    ),
}
# L1SI170-COPLIB-008：六件已去编号改写并自查零命中，显式排除整组撤除；
# _DENY_PATHS 机制保留（空表），后续精确排除仍走此前置通道。
_DENY_PATHS = {
    "cop-library": frozenset(),
}
_DENY_SET = frozenset(n for names in _DENY_PATHS.values() for n in names)
_PUBLIC_SET = frozenset(n for names in _PUBLIC_DOCS.values() for n in names)
_PUBLIC_FAMILY = {n: fam for fam, names in _PUBLIC_DOCS.items() for n in names}

# L1SI154-011 段C：清单显示名映射（⛔ 只改显示名，路径与 slug 一字不改，防断链）。
# 背景：008 段A 只换了六件内容、件名未变，文件名里的 V0.1-DRAFT 与内容面貌（V1.0-FROZEN已生效）
# 不符；相遇专章按 L1SI176 REPO-MAIN-SETTLE-001 §三取甲更正：对外通用件 CORPUS-059 真名在册，
# 条例本体（STD-SCENE-ENCOUNTER-001）留 docs/regulations/ 但⛔不入白名单——内部条例号自己用，名字不互借。
# 键必须是 _PUBLIC_SET 内的在册件名；未映射件显示名=文件名（默认行为不变）。
_DISPLAY_NAME = {
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（单一权威稿·中文人读版V1.0-FROZEN）.md":
        "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（单一权威稿·中文人读版·V1.0-FROZEN已生效）.md",
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（英文人读版V1.0-FROZEN）.md":
        "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（英文人读版·V1.0-FROZEN已生效）.md",
    "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（机读版V1.0-FROZEN）.yaml":
        "TDCA-SPEC-CONFIGMARKET-001-配置权市场规范（机读版·V1.0-FROZEN已生效）.yaml",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（中文人读版V1.0-FROZEN）.md":
        "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（中文人读版·V1.0-FROZEN已生效）.md",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（英文人读版V1.0-FROZEN）.md":
        "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（英文人读版·V1.0-FROZEN已生效）.md",
    "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（机读版V1.0-FROZEN）.yaml":
        "TDCA-SPEC-REGISTER-OF-RIGHTS-001-TDCA注册登记制度（机读版·V1.0-FROZEN已生效）.yaml",
    # 相遇专章取甲：键＝在册件名 CORPUS-059 真名（自映射占位，口径见文件头注）
    "TDCA-PUB-CORPUS-059-场景线相遇专章对外版单独件（V1.0已生效·十七条·供站上替换旧草案版）.md":
        "TDCA-PUB-CORPUS-059-场景线相遇专章对外版单独件（V1.0已生效·十七条·供站上替换旧草案版）.md",
    # L1SI154-081：去内部批次字样（卷二纯版第N批…），显示名规则＝制度名（形态·版本）；slug/路径不动
    "TDCA-PUB-CORPUS-029-卷二纯版第二批清理版重出-身份可信等级认定条例对外版（仅去符号·语义同028·六检通过）.md":
        "TDCA-PUB-CORPUS-029-身份可信等级认定条例对外版（V1.0已生效）.md",
    "TDCA-PUB-CORPUS-030-卷二纯版第三批-智能体定义条例对外版（二十一条·V1.0已生效·六检通过·引用不重写）.md":
        "TDCA-PUB-CORPUS-030-智能体定义条例对外版（V1.0已生效·二十一条）.md",
    # L1SI154-028：六卡三卷入册（显示名加「流程卡 ·」「说明卷 ·」前缀；slug/路径不动）
    "TDCA-PUB-CORPUS-083-流程环节卡发现（五问·六类失败·第4张卡）.md":
        "流程卡 · 发现（五问 · 六类失败）.md",
    "TDCA-PUB-CORPUS-084-流程环节卡相遇（五问·六类失败·第5张卡）.md":
        "流程卡 · 相遇（五问 · 六类失败）.md",
    "TDCA-PUB-CORPUS-085-流程环节卡握手（五问·七类失败·第6张卡）.md":
        "流程卡 · 握手（五问 · 七类失败）.md",
    "TDCA-PUB-CORPUS-086-流程环节卡签约（五问·七类失败·第7张卡）.md":
        "流程卡 · 签约（五问 · 七类失败）.md",
    "TDCA-PUB-CORPUS-087-流程环节卡交付（五问·七类失败·第8张卡）.md":
        "流程卡 · 交付（五问 · 七类失败）.md",
    "TDCA-PUB-CORPUS-088-流程环节卡验收（五问·七类失败·第9张卡）.md":
        "流程卡 · 验收（五问 · 七类失败）.md",
    "TDCA-PUB-CORPUS-090-卷四治理卷对外版（谁定规则与怎么改与怎么监督与争议边界·首件）.md":
        "说明卷 · 卷四 治理卷（谁定规则／怎么改／怎么监督／争议边界）.md",
    "TDCA-PUB-CORPUS-091-卷五同构卷对外版（制度与技术同构与本体同构与场景嵌套·移植四步·边界四条）.md":
        "说明卷 · 卷五 同构卷（制度与技术同构／本体同构／场景嵌套）.md",
    "TDCA-PUB-CORPUS-092-卷六助手与入口对外版（三类入口与助手四步接入与代签红线）.md":
        "说明卷 · 卷六 助手与入口（三类入口／助手四步接入／代签红线）.md",
}
assert all(n in _PUBLIC_SET for n in _DISPLAY_NAME), "显示名映射键必须是在册件名"

_RATE_LIMIT_PER_MIN = 60

# ---------------------------------------------------------------------
# 限流（进程内滑动窗口；单 worker 部署下足够，防枚举非防攻击）
# ---------------------------------------------------------------------
_hits: dict[str, list] = {}
_hits_lock = threading.Lock()


def _rate_limited(ip: str) -> bool:
    now = time.monotonic()
    with _hits_lock:
        lst = _hits.setdefault(ip, [])
        cutoff = now - 60.0
        while lst and lst[0] < cutoff:
            lst.pop(0)
        if len(lst) >= _RATE_LIMIT_PER_MIN:
            return True
        lst.append(now)
        return False


# ---------------------------------------------------------------------
# 件目录解析：容器内只读挂载（/docs/<族目录>）为单一事实源；
# 本地/测试可用 TDCA_PUBLIC_DOCS_DIR 指向等价目录（⛔ 生产不设）
# ---------------------------------------------------------------------
def _docs_dir(family: str = _FAMILY) -> Path | None:
    override = os.environ.get("TDCA_PUBLIC_DOCS_DIR", "").strip()
    if override:
        # 测试覆盖：所有族共用一个等价目录（夹具平铺全部在册件）
        p = Path(override)
        return p if p.is_dir() else None
    sub = _FAMILY_DIRS.get(family)
    if not sub:
        return None
    here = Path(__file__).resolve()
    for parent in (here.parents[3], here.parents[2], here.parents[1]):
        cand = parent / "docs" / sub
        if cand.is_dir():
            return cand
    return None


def _read_doc(filename: str) -> tuple[bytes, str] | None:
    """读在册公开件（⛔ 绝不越出清单）；返回 (bytes, sha256) 或 None。"""
    if filename in _DENY_SET:  # L1SI170-COPLIB-007：显式排除前置，硬 404
        return None
    if filename not in _PUBLIC_SET:
        return None
    d = _docs_dir(_PUBLIC_FAMILY.get(filename, _FAMILY))
    if d is None:
        return None
    fpath = d / filename
    try:
        raw = fpath.read_bytes()
    except OSError:
        return None
    # 纵深防御（防路径穿越）：白名单件可含子路径（cop-library 族），解析后须仍在族目录内
    try:
        if not fpath.is_file() or not fpath.resolve().is_relative_to(d.resolve()):
            return None
    except OSError:
        return None
    return raw, hashlib.sha256(raw).hexdigest()


_VERSION_RE = re.compile(r"V\d+\.\d+(?:-[A-Z0-9.]+)*")
_YAML_VERSION_RE = re.compile(r"^version:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", re.M)


def _version_of(filename: str, text: str) -> str | None:
    """版本读件内真实值（best-effort；⛔ 不硬编码）。"""
    if filename.endswith(".yaml"):
        m = _YAML_VERSION_RE.search(text[:2000])
        if m:
            return m.group(1).strip()
    head = "\n".join(text.splitlines()[:30])
    m = _VERSION_RE.search(head)
    return m.group(0) if m else None


def _entry(filename: str, raw: bytes, sha: str, family: str) -> dict:
    text = raw.decode("utf-8", "replace")
    return {
        "family": family,
        "slug": filename,
        "filename": filename,
        "display_name": _DISPLAY_NAME.get(filename, filename),  # 仅显示层；路径/slug 不改
        "version": _version_of(filename, text),
        "bytes": len(raw),
        "sha256": sha,
        "sha256_16": sha.upper()[:16],
    }


def _list_docs(family: str = _FAMILY) -> JSONResponse:
    entries = []
    for name in _PUBLIC_DOCS.get(family, ()):  # 未知族：空清单（路由层已 404，纵深防御）
        got = _read_doc(name)
        if got is None:
            # 已入站件缺失＝容器件异常：不静默减项，明示 fail-closed
            # L1SI153 段三②：error 机器字段设过渡期（两存：error＋detail＋code）——
            # DEPRECATED，下版删除；新判据一律读 code，⛔ 勿为新代码依赖 error
            return JSONResponse(
                with_code({"error": "DOC_SOURCE_UNAVAILABLE",
                           "detail": f"在册公开件暂不可读：{name}（文档源异常，已按 fail-closed 暂停列出）"}, 503),
                status_code=503)
        raw, sha = got
        entries.append(_entry(name, raw, sha, family))
    return JSONResponse({
        "family": family,
        "count": len(entries),
        "source": f"docs/{_FAMILY_DIRS.get(family, family)}（只读容器件·单一事实源）",
        "principle": "只列已入站公开件；未入站与存证件不出现（fail-closed）",
        "documents": entries,
    })


def _get_doc(slug: str, family: str | None = None) -> JSONResponse:
    # L1SI170-COPLIB-007：slug 须属所请求之族（新族含 README.md 等通用名，防跨族串读）
    if family is not None and _PUBLIC_FAMILY.get(slug) != family:
        return JSONResponse(with_code({"detail": "该文档不存在或未公开"}, 404), status_code=404)
    got = _read_doc(slug)
    if got is None:
        # 统一 404：未入站件／乙类件／不存在件，对外不可分辨（fail-closed）
        # L1SI153 段二②：裸英文退役 → 中文短句＋码
        return JSONResponse(with_code({"detail": "该文档不存在或未公开"}, 404), status_code=404)
    raw, sha = got
    entry = _entry(slug, raw, sha, _PUBLIC_FAMILY.get(slug, _FAMILY))
    entry["content"] = raw.decode("utf-8", "replace")
    return JSONResponse(entry)


def _guard(request: Request) -> JSONResponse | None:
    if _rate_limited(request.client.host if request.client else "unknown"):
        # L1SI153 段二②：裸英文退役 → 码表口径中文短句（RES-RES-001）
        return JSONResponse(with_code({"detail": "操作过于频繁，请稍后再试（限流 60 次/分钟/同一地址）"}, 429), status_code=429)
    return None


# ---------------------------------------------------------------------
# 主路由：GET /api/public/docs[/regulation[/slug]]
# ---------------------------------------------------------------------
@router.get("/docs")
def public_docs_list(request: Request):
    blocked = _guard(request)
    if blocked is not None:
        return blocked
    return _list_docs()


@router.get("/docs/{family}")
def public_docs_family(family: str, request: Request):
    blocked = _guard(request)
    if blocked is not None:
        return blocked
    if family not in _PUBLIC_DOCS:
        # L1SI154-010：族按公开清单判定（⛔ 非清单族一律 fail-closed 404）
        # L1SI153 段二②：裸英文退役 → 中文短句＋码
        return JSONResponse(with_code({"detail": "该文档不存在或未公开"}, 404), status_code=404)
    return _list_docs(family)


@router.get("/docs/{family}/{slug:path}")
def public_docs_get(family: str, slug: str, request: Request):
    blocked = _guard(request)
    if blocked is not None:
        return blocked
    if family not in _PUBLIC_DOCS:
        # L1SI154-010：族按公开清单判定（⛔ 非清单族一律 fail-closed 404）
        # L1SI153 段二②：裸英文退役 → 中文短句＋码
        return JSONResponse(with_code({"detail": "该文档不存在或未公开"}, 404), status_code=404)
    return _get_doc(slug, family)


# ---------------------------------------------------------------------
# 别名：旧 /api/site/docs/* —— 同一实现，⛔ 不双实现（施工令 §二）
# ---------------------------------------------------------------------
@alias_router.get("/docs")
def alias_docs_list(request: Request):
    return public_docs_list(request)


@alias_router.get("/docs/{family}")
def alias_docs_family(family: str, request: Request):
    return public_docs_family(family, request)


@alias_router.get("/docs/{family}/{slug:path}")
def alias_docs_get(family: str, slug: str, request: Request):
    return public_docs_get(family, slug, request)
