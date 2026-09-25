# -*- coding: utf-8 -*-
"""工程三协议系列批量编译器 (TDCA 原生系列思维协议)
依据: 编译清单-工程三协议系列-2026-08-30.md (v2: 41 COP = 25 原生 + 16 化合)
裁定: 用户 2026-08-30 20:48 —— 全量编译 / 场景 COP 允许换绑 / F1 拆分为 4
原则: 组合性强制 (standalone=false) / TDCA 体系内 base_protocol=TDCA-CORE 强制遵守 /
      TDCA 原生系列, 剥离 TDCA 治理层后协议语义独立自洽 (可移植)
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
纪律: 只产 yaml 至本工作区, 零推送零外部写入; 每 COP 携带 ⊗ 负空间与 NSFL 通用禁忌
"""
import os
import sys
import json
import datetime
import hashlib

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "config"))
sys.path.insert(0, os.path.join(_THIS, "..", "nca-generator"))
sys.path.insert(0, _THIS)

import tdca_config as TC
import cognitive_compiler as CC
import nca_generator as NCA

ensure_dirs = TC.ensure_dirs
NSFL_VERSION = TC.NSFL_VERSION
BASE = os.path.join(_THIS, "engineering-three")
ensure_dirs()
for sub in ("trial", "grey", "dependability", "fusion", "fusion_scene", "fusion_tdca"):
    os.makedirs(os.path.join(BASE, sub), exist_ok=True)

COMPOSITION_POLICY = {
    "standalone": False,
    "tdca_native": True,
    "mandatory_base": "TDCA-CORE (TDCA 体系内强制遵守, 不可配置关闭)",
    "detachable": "剥离 TDCA 治理层后协议语义保持独立自洽, 可移植至其他治理体系",
    "note": "思维协议不是独立发挥作用的, 须与系列内其他 COP 组合调用 (用户裁定 2026-08-30)",
    # 正典宪法 (单一事实源: 编译清单第 5/5b 条; 2026-08-30 REASONIX 审查项②修复统一)
    "constitution": "NSFL 否决权 (F1.5, 用户裁定 2026-08-30 21:07): 对于任何无法通过 NSFL 预检的事件 (负空间触碰), 即使其他四判据全部通过, 亦视为整体拒绝 (Fail-Closed); NSFL 预检的优先级永远高于其他四判据——负空间是安全宪法的宪法, 不可配置关闭, 不可被多数判据推翻。四态动态处置 (F1.5b, 用户裁定 2026-08-30 21:19): TDCA 是动态管理, 负空间本质保守不轻易变化但仍会演化——现在触犯不等于永远触犯; 否决权的不可推翻性仅指即时门控裁决, 不指永恒身份; sandbox 检验触犯负空间的实体走四态处置: 休眠/禁止/重塑/出清 (裁定 NCA 存证, 禁悬置), 负空间版本更新时休眠/重塑态强制重评",
}

COMMON_NEG_EXTRA = [
    "⊗ 禁止脱离组合单独调用: 本协议非独立发挥作用, 须与系列内其他 COP 组合",
    "⊗ 禁止违反 NSFL: 伦理/法律负空间不可越",
    "⊗ 禁止 NSFL 否决权被推翻: NSFL 预检未过的事件, 禁止以其余判据全部通过、多数决、场景豁免、上级指令等任何理由放行 (F1.5 宪法条款, Fail-Closed, 不可配置关闭)",
    "⊗ 禁止把否决当终审: 否决只封锁当下过门资格, 不判处永恒身份——触犯实体须进入四态动态处置 (休眠/禁止/重塑/出清), 禁止悬置不处置; 负空间版本演化时, 休眠/重塑态实体须重新评估 (TDCA 动态管理, 用户裁定 2026-08-30 21:19)",
]


# ---------- 原生 COP (A/B/C 组) ----------
def build_native(prefix, idx, name, pinyin, core, precond, steps, neg, related):
    fn = pinyin
    prim = {
        "name": fn,
        "method": name,
        "signature": "fn %s(context: Situation) -> Outcome" % fn,
        "precond": precond,
        "postcond": core + " (目标达成)",
        "negative_space": "⊗ " + neg,
        "steps": steps,
        "nca_emit": True,
    }
    cop = {
        "COP-ID": "%s-COP-20260830-%02d" % (prefix, idx),
        "source_expert": "engineering-three (试验×灰度×可靠性)",
        "compiler": "cognitive_compiler (T1+T2 规范复用)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "group": prefix,
        "base_protocol": "TDCA-CORE",
        "composition_policy": dict(COMPOSITION_POLICY),
        "soul": {
            "identity": name,
            "core": core,
            "role": "TDCA 原生系列思维协议 (工程三部曲)",
            "category": "工程三协议 / " + prefix,
        },
        "primitives": [prim],
        "dispatch": {
            "main_pipeline": fn,
            "graph": [{"from": fn, "to": related}],
            "note": "主原语 %s 即该细分思维执行体; to=系列内组合调用项 (组合性强制)" % fn,
        },
        "decision": [{"if": precond, "call": fn}],
        "skills": [],
        "negative_space": ["⊗ " + neg] + COMMON_NEG_EXTRA,
        "nsfl_version": NSFL_VERSION,
    }
    CC.s5_validate(cop)
    return cop


# ---------- 化合 COP (D/E/F 组, interpretant 绑定 + 属性改变模式) ----------
# 用户判据 (2026-08-30 20:52): 化合=改变属性产生新思维; 叠加不改变属性=只是两个独立思维的合作。
# 故每个化合 COP 强制携带 fusion_spec: 属性改变表 + 涌现物判据; 签名/前后置/步骤在化合层重写, 非拼接。

FUSION_SPEC_RULE = ("化合=改变属性、产生新思维; 叠加不改变属性、只产生两个独立思维的合作。"
                    "本 COP 声明 fusion_type=化合, 以 attribute_changes 为证; 无属性改变的组合须降级标注为合作。")


def build_composed(cid, name, fn, parents, interpretants, core, precond, steps, neg, related, fusion_spec):
    """interpretants: [{cop_id, name, bind_step, effect}]
    fusion_spec: {"attribute_changes": [{attribute, before, after}], "emergence": str}"""
    prim = {
        "name": fn,
        "method": "%s (化合产物, 属性已改变: %s)" % (name, "; ".join(
            "%s: %s→%s" % (a["attribute"], a["before"], a["after"]) for a in fusion_spec["attribute_changes"])),
        "signature": "fn %s(fused: CompoundContext) -> EmergentOutcome" % fn,
        "precond": "化合前置: " + precond + " (反应物 COP 已就位且组合性强制成立)",
        "postcond": core + " (涌现达成: " + fusion_spec["emergence"] + ")",
        "negative_space": "⊗ " + neg,
        "steps": steps,
        "nca_emit": True,
    }
    interp_objs = [
        {
            "cop_id": i["cop_id"],
            "relation": "反应物 (解释项, 属性被改变)",
            "bind_step": i["bind_step"],
            "effect": i["effect"],
        }
        for i in interpretants
    ]
    cop = {
        "COP-ID": cid,
        "type": "COMPOUND-COP",
        "source_expert": "engineering-three (双层化合: 工程三⊗场景⊗TDCA)",
        "compiler": "cognitive_compiler (T1+T2 规范复用, 化合模式: 属性改变+涌现判据)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "composition": {
            "parent": parents,
            "interpretants": interp_objs,
            "bind_policy": "绑定关系为运用层配置, 运行期允许换绑 (用户裁定 2026-08-30)",
        },
        "fusion_spec": {
            "fusion_type": "化合",
            "verdict_rule": FUSION_SPEC_RULE,
            "attribute_changes": fusion_spec["attribute_changes"],
            "emergence": fusion_spec["emergence"],
        },
        "base_protocol": "TDCA-CORE",
        "composition_policy": dict(COMPOSITION_POLICY),
        "soul": {
            "identity": name,
            "core": core,
            "role": "TDCA 原生系列思维协议 (化合层, 新思维)",
            "category": "工程三协议化合 / " + name,
        },
        "primitives": [prim],
        "dispatch": {
            "main_pipeline": fn,
            "graph": [
                {"from": fn, "to": [i["cop_id"] for i in interpretants] + related,
                 "note": "父原语在绑定步与反应物化合——反应物属性被改变, 涌现出反应物各自不具备的新思维 (非叠加合作)"}
            ],
            "note": "化合≠叠加: 叠加不改变属性只是两个独立思维的合作; 本 COP 的组合语义以 fusion_spec.attribute_changes 为证",
        },
        "decision": [{"if": precond, "call": fn}],
        "skills": [],
        "negative_space": ["⊗ " + neg,
                           "⊗ 禁止叠加冒充化合: 组合后若无属性改变、无新思维涌现, 须降级标注为'合作'而非'化合'"]
                          + COMMON_NEG_EXTRA,
        "nsfl_version": NSFL_VERSION,
    }
    CC.s5_validate(cop)
    return cop


# ================= 知识库 =================
# A 组: 试验思维 (8)
TRIAL = [
    ("惟一差异原则", "wei_yi_cha_yi", "观察到的效应只能归因于被研究因子, 其余条件全同",
     "需要因果结论且存在可操控处理因子",
     ["固定其余条件全同", "仅操控目标因子", "设置对照组", "效应唯一归因"],
     "存在未控制混杂变量时不得下因果结论", ["wu_cha_san_zhi_zhu", "trial_check_gate"]),
    ("误差控制三支柱", "wu_cha_san_zhi_zhu", "重复估误差、随机化消偏差、局部控制降异质",
     "试验存在不可消除的随机误差与系统偏差",
     ["重复足够试验单元以估计误差", "随机化分配处理消偏差", "按异质性来源分区组局部控制"],
     "禁伪重复: 试验单元≠测量单元", ["wei_yi_cha_yi", "bian_yi_fen_jie"]),
    ("试验生命周期四阶段", "trial_lifecycle", "探索→析因→优化→验证, 各阶段配对设计策略",
     "研究问题处于不同成熟度",
     ["探索阶段筛选因子", "析因阶段分解交互", "优化阶段寻最优组合", "验证阶段确认结论"],
     "禁跳过验证期直接外推结论", ["she_ji_xuan_ze_jue_ce_shu", "trial_check_gate"]),
    ("设计选择决策树", "she_ji_xuan_ze_jue_ce_shu", "按异质性来源/因子数/实施约束选设计",
     "需在 CRD/RCBD/拉丁方/BIBD/裂区 间选型",
     ["识别异质性来源", "清点因子数与水平数", "评估实施约束", "沿决策树选定设计"],
     "禁表头设计不当致主效与低阶互作混杂", ["bian_yi_fen_jie", "trial_lifecycle"]),
    ("变异分解思维", "bian_yi_fen_jie", "总变异=处理+区组+误差, 强制顺序分析",
     "已获得设计试验数据待分析",
     ["平方和分解", "自由度对应", "F 检验按强制顺序", "事后多重比较校正族错误率"],
     "禁事后多重比较不校正族错误率", ["wu_cha_san_zhi_zhu", "wen_jian_xing_ping_gu"]),
    ("稳健性评估思维", "wen_jian_xing_ping_gu", "信噪比+质量损失函数 (望目/望大/望小)",
     "参数优化需抗噪声干扰",
     ["定义质量特性望目/望大/望小", "计算信噪比", "内外表设计", "择稳健参数组合"],
     "禁只看均值不看变异", ["bian_yi_fen_jie", "she_ji_xuan_ze_jue_ce_shu"]),
    ("试验陷阱防御", "shi_yan_xian_jing_fang_yu", "识别伪重复/混杂/多重比较/过度外推四陷阱",
     "试验结论待审",
     ["核对试验单元与测量单元", "排查混杂变量", "校正多重比较", "界定外推边界"],
     "禁将模型结论外推至试验范围外", ["wei_yi_cha_yi", "trial_check_gate"]),
    ("试验检查门控", "trial_check_gate", "设计前/中/实施后/结论后四道清单门",
     "试验全流程需质量门控",
     ["设计前清单门", "实施中清单门", "实施后清单门", "结论后清单门"],
     "禁门控项未过即进入下一阶段", ["shi_yan_xian_jing_fang_yu", "trial_lifecycle"]),
]

# B 组: 灰度管理 (9)
GREY = [
    ("灰度世界观", "hui_du_shi_jie_guan", "承认贫信息是常态, 白/灰/黑三态定策",
     "面对信息不完全的决策局面",
     ["评估信息灰度等级", "白/灰/黑三态归类", "按态选策"],
     "禁数据洁癖: 等数据完美即错失窗口", ["bai_hua_shou_lian", "hui_ba_jue_ce"]),
    ("白化收敛思维", "bai_hua_shou_lian", "渐进白化、灰度递减、层次推进",
     "灰问题需向白转化",
     ["界定当前灰度", "设计白化路径", "分层推进", "校验白化收益"],
     "禁白化过度: 虚假精确误导决策", ["hui_du_shi_jie_guan", "gun_dong_bai_hua"]),
    ("冲击扰动缓冲", "chong_ji_ren_dong_huan_chong", "数据≠事实, 先净化 (缓冲算子) 再建模",
     "序列含异常冲击或观测扰动",
     ["识别冲击扰动点", "施加缓冲算子净化", "比对净化前后", "再建模"],
     "禁把扰动噪声当系统趋势建模", ["xu_lie_sheng_cheng", "gm_jian_mo_jue_ce"]),
    ("序列生成思维", "xu_lie_sheng_cheng", "均值/级比/AGO/IAGO 四算子转化贫信息",
     "少数据序列待生成处理",
     ["均值检验", "级比检验", "AGO 生成", "IAGO 还原验证"],
     "禁未过光滑性/级比检验强行建模", ["gm_jian_mo_jue_ce", "hui_se_guan_lian"]),
    ("灰色关联分析", "hui_se_guan_lian", "五步法定关联序, 看排序不看绝对值",
     "多因素对目标影响强弱需排序",
     ["确定参考序列", "无量纲化", "求关联系数", "求关联度", "排关联序"],
     "禁纠结关联度绝对值大小", ["ju_lei_ping_gu", "xu_lie_sheng_cheng"]),
    ("灰色聚类评估", "ju_lei_ping_gu", "三角白化权函数柔性分级, 变权/定权按场景",
     "对象需按多个灰类指标分级",
     ["定灰类与白化权函数", "变权/定权选型", "计算聚类系数", "柔性分级判定"],
     "禁灰类边界僵化 (标签一刀切)", ["hui_se_guan_lian", "hui_ba_jue_ce"]),
    ("GM建模决策", "gm_jian_mo_jue_ce", "五步建模强制流程+模型族决策树+适用红线",
     "需用灰色模型预测或决策",
     ["级比检验", "GM(1,1) 基础建模", "残差检验", "按决策树选模型族", "适用红线核对"],
     "禁全场景套用GM(1,1); 禁单一模型定论", ["xu_lie_sheng_cheng", "gun_dong_bai_hua"]),
    ("灰靶决策思维", "hui_ba_jue_ce", "目标是区间不是点; 状态与趋势双评估",
     "多目标决策容许满意区间",
     ["定靶心与靶界", "计算靶心距", "状态与趋势双评估", "区间决策"],
     "禁静态截面一次性决策", ["gm_jian_mo_jue_ce", "gun_dong_bai_hua"]),
    ("滚动白化控制", "gun_dong_bai_hua", "预测→执行→观测→修正闭环, 前馈+反馈",
     "系统需持续控制且信息渐进白化",
     ["GM 预测", "执行", "观测偏差", "前馈+反馈修正", "下一轮滚动"],
     "禁一次性校正后不再复盘", ["hui_ba_jue_ce", "bai_hua_shou_lian"]),
]

# C 组: 可靠性设计 (8)
DEP = [
    ("设计预防公理", "she_ji_yu_fang", "可信性是设计出来的: 1元预防省10-100元纠正 (LCC)",
     "产品/系统处于概念设计期",
     ["需求即含可信性指标", "LCC 全周期权衡", "设计预防优先于事后纠正"],
     "禁试验依赖症: 先造出来坏了再改", ["quan_sheng_ming_zhou_qi", "xi_tong_xiao_neng_quan_heng"]),
    ("系统效能权衡", "xi_tong_xiao_neng_quan_heng", "效能=A×D×C, 禁单指标最优",
     "多指标间存在张力需权衡",
     ["可用度 A 建模", "可信度 D 建模", "能力 C 建模", "乘积效能 Pareto 权衡"],
     "禁为MTBF牺牲维修性/可用性/能力", ["she_ji_yu_fang", "rong_cuo_jiang_e"]),
    ("全生命周期协议", "quan_sheng_ming_zhou_qi", "概念→设计→生产→使用→退役五阶段各有强制动作",
     "系统处于任一生命周期阶段",
     ["概念阶段论证", "设计阶段评审", "生产阶段质控", "使用阶段保障", "退役阶段处置"],
     "禁设计评审跳级; 禁验证即终点", ["she_ji_yu_fang", "shi_xiao_shu_ju_bi_huan"]),
    ("失效模式分析", "shi_xiao_mo_shi_fen_xi", "FMEA自下而上+FTA自上而下双向夹击",
     "系统失效风险需系统排查",
     ["FMEA 逐件枚举失效模式与严酷度", "FTA 以顶事件向下分解最小割集", "双向夹击闭环"],
     "禁FMEA不覆盖Ⅰ/Ⅱ类严酷度故障", ["rong_cuo_jiang_e", "shi_xiao_shu_ju_bi_huan"]),
    ("容错降额设计", "rong_cuo_jiang_e", "降额/冗余/优雅降级/BIT自监控",
     "关键功能需在高应力下保可用",
     ["关键单元降额", "冗余配置", "优雅降级路径", "BIT 自监控"],
     "禁容错不覆盖单点故障", ["shi_xiao_mo_shi_fen_xi", "xi_tong_xiao_neng_quan_heng"]),
    ("建模预计决策", "jian_mo_yu_ji", "串/并/表决建模树+预计方法按阶段选",
     "可靠性指标需分配与预计",
     ["可靠性框图建模", "预计方法按阶段选", "指标分配", "可达性核对"],
     "禁指标虚高: 规定MTBF超技术可达", ["xi_tong_xiao_neng_quan_heng", "zeng_chang_yan_zheng_fen_li"]),
    ("增长验证分离", "zeng_chang_yan_zheng_fen_li", "RGT允许边试边改, RQT禁止, 改后须独立复验",
     "可靠性试验需区分增长与验证",
     ["标记试验态 RGT/RQT", "RGT 允许边试边改", "RQT 冻结设计独立复验"],
     "禁在RQT中边测边改致统计失效", ["shi_xiao_shu_ju_bi_huan", "quan_sheng_ming_zhou_qi"]),
    ("失效数据闭环", "shi_xiao_shu_ju_bi_huan", "FRACAS+FRB: 失效必报告→分析→纠正→验证→标准化",
     "运行期失效事件持续发生",
     ["失效强制报告", "FRB 分析", "纠正措施", "验证", "标准化入知识库"],
     "禁数据沉睡: 录入后无人分析", ["shi_xiao_mo_shi_fen_xi", "zeng_chang_yan_zheng_fen_li"]),
]

# D 组: 三者化合 (5)
FUSION = [
    ("COMPOSED-AGENTSAFETY-20260830-01", "智能体安全管理总纲", "agent_safety_fusion",
     ["TRIAL-COP-20260830-01..08", "GREY-COP-20260830-01..09", "DEP-COP-20260830-01..08"],
     [("场景七元组", "全局", "安全目标由场景涌现并确权, 非悬空指标")],
     "四公理: 安全是涌现属性/边界是灰区间/须受控对抗试验验证/失效数据闭环驱动进化",
     "智能体系统需要全生命周期安全治理",
     ["安全是涌现属性非单体堆砌", "安全边界灰化区间化", "安全须受控对抗试验验证", "失效数据闭环驱动进化"],
     "禁把安全当单体属性堆砌; 禁静态安全观",
     ["concept_grey_definition", "fault_tolerant_architecture", "controlled_adversarial_trial", "grey_deployment_monitoring"]),
    ("COMPOSED-AGENTSAFETY-20260830-02", "概念灰化定义", "concept_grey_definition",
     ["GREY-COP-20260830-01", "GREY-COP-20260830-08", "DEP-COP-20260830-02", "DEP-COP-20260830-03"],
     [("场景七元组", "灰化定义阶段", "灰靶区间按场景依存效用定义, 拒绝全局常数")],
     "安全需求灰化为灰靶区间, 任务剖面分析+安全指标分配+四维Pareto权衡",
     "智能体安全需求处于概念期",
     ["将绝对安全转化为灰靶区间", "任务剖面分析", "安全指标分配", "性能-安全-成本-可解释四维权衡"],
     "禁精确安全执念; 禁指标分配无剖面依据",
     ["scene_relativity_of_target", "fault_tolerant_architecture"]),
    ("COMPOSED-AGENTSAFETY-20260830-03", "容错架构设计", "fault_tolerant_architecture",
     ["DEP-COP-20260830-04", "DEP-COP-20260830-05", "TRIAL-COP-20260830-03"],
     [("场景七元组", "架构设计阶段", "FMEA 沿场景画布六要素展开, 割集沿嵌套链分解")],
     "智能体FMEA (幻觉/注入/滥用/级联) +FTA+watchdog+HITL熔断+设计评审不可跳过",
     "安全架构待设计",
     ["智能体FMEA 枚举失效模式", "FTA 分解根因", "独立watchdog+HITL熔断", "设计评审不可跳过"],
     "禁单点测试谬误; 禁黑箱信任",
     ["canvas_profiling_fmea", "nested_fault_propagation", "controlled_adversarial_trial"]),
    ("COMPOSED-AGENTSAFETY-20260830-04", "受控对抗试验", "controlled_adversarial_trial",
     ["TRIAL-COP-20260830-01", "TRIAL-COP-20260830-02", "TRIAL-COP-20260830-04", "GREY-COP-20260830-03", "DEP-COP-20260830-07"],
     [("场景七元组", "对抗试验阶段", "攻击向量筛选须覆盖场景应力, 非理想环境")],
     "分式/正交筛选攻击向量+惟一差异A/B+冲击扰动试验+TAAF增长循环 (RGT态)",
     "安全机制效果待验证",
     ["分式因子设计筛选攻击向量", "正交表安排多因素攻击试验", "惟一差异 A/B 检验", "冲击扰动试验", "TAAF 增长循环 (RGT 态)"],
     "禁混淆增长与验证; 禁伪重复",
     ["emergent_risk_watch", "grey_deployment_monitoring"]),
    ("COMPOSED-AGENTSAFETY-20260830-05", "灰度部署监控", "grey_deployment_monitoring",
     ["GREY-COP-20260830-07", "GREY-COP-20260830-09", "DEP-COP-20260830-08", "TRIAL-COP-20260830-08"],
     [("场景七元组", "部署监控阶段", "灰度节奏与监控阈值随场景阶段共适配")],
     "灰度发布 (区组控制) +AGO序列监控+灾变预警+关联监控+FRACAS闭环 (RQT态)",
     "已验证智能体待上线",
     ["小流量→中流量→全量区组发布", "AGO 序列监控+GM(1,1) 趋势预测", "灾变预警", "关联监控", "FRACAS 闭环 (RQT 态)"],
     "禁数据沉睡; 禁一次性校正后不再复盘",
     ["lifecycle_co_adaptation", "governed_fracas", "mou_grey_target_fuse"]),
]

# E 组: 工程三 ⊗ 场景 (7)
SCEN_DIR = "SCEN-COP-20260814"
SCENE_FUSION = [
    ("COMPOSED-SCENESAFETY-20260830-01", "场景依存灰靶", "scene_relativity_of_target",
     "COMPOSED-AGENTSAFETY-20260830-02",
     ("01", "场景思维协议"), "定义灰靶区间之前先界定场景归属",
     "灰靶=f(场景), 场景变→灰靶漂移是规则不是例外",
     "安全指标需设容忍区间",
     ["界定场景归属 (参与者网络/资源流动/价值流)", "按场景定灰靶区间并打场景标签 target(scene)", "场景变→灰靶重定义"],
     "禁跨场景复用灰靶; 禁场景未界定就定灰靶",
     ["lifecycle_co_adaptation", "mou_grey_target_fuse"]),
    ("COMPOSED-SCENESAFETY-20260830-02", "画布剖面FMEA", "canvas_profiling_fmea",
     "COMPOSED-AGENTSAFETY-20260830-03",
     ("02", "场景画布"), "枚举失效模式时按六要素逐格扫描",
     "FMEA 沿画布六要素展开, 失效注入点带场景坐标",
     "智能体失效模式待系统排查",
     ["画布六要素逐格扫描 (参与者/资源/规则/架构/价值流/意义)", "按格枚举失效注入点", "产出带场景坐标的失效模式矩阵"],
     "禁脱离画布的通用模板套用; 六要素缺一结论不可信",
     ["nested_fault_propagation", "shapley_safety_attribution"]),
    ("COMPOSED-SCENESAFETY-20260830-03", "涌现风险监控", "emergent_risk_watch",
     "COMPOSED-AGENTSAFETY-20260830-05",
     ("03", "认知涌现"), "关联度矩阵后增加涌现检验",
     "监控智能体间关联度的涌现结构 (无业务解释的同步偏离)",
     "多智能体运行中需识别协同异常",
     ["计算关联度矩阵", "对照业务基线检验涌现结构", "识别无业务解释的同步偏离", "超界触发认知对齐门复查"],
     "禁缺业务基线对照误判共谋; 禁只看单体指标遗漏涌现层",
     ["aligned_cognition_gate", "hui_se_guan_lian"]),
    ("COMPOSED-SCENESAFETY-20260830-04", "嵌套失效传播", "nested_fault_propagation",
     "COMPOSED-AGENTSAFETY-20260830-03",
     ("04", "嵌套法则"), "FTA 向下分解时按嵌套七元组逐层展开",
     "割集沿嵌套链走, 嵌套调用须携带 MOU 校验 (L2 硬约束)",
     "系统级失效需根因分解",
     ["按嵌套七元组逐层展开 FTA", "量化深层嵌套对顶事件贡献", "嵌套链强制 MOU 校验", "产出嵌套级联割集表"],
     "禁 FTA 只展开两层即定根因; 禁嵌套链无 MOU 校验放行",
     ["shapley_safety_attribution", "fault_tolerant_architecture"]),
    ("COMPOSED-SCENESAFETY-20260830-05", "生命周期共适配", "lifecycle_co_adaptation",
     "COMPOSED-AGENTSAFETY-20260830-05",
     ("05", "生命周期适配"), "滚动白化每轮先判场景阶段漂移",
     "场景阶段决定安全策略重心, 漂移超限回灰靶重定义",
     "场景演化中需持续控制",
     ["每轮滚动修正先判场景阶段", "阶段决定策略重心 (萌芽重灰化/成长重试验/成熟重监控/衰退重退役)", "漂移超限触发灰靶重定义"],
     "禁场景新阶段配旧策略 (错配=风险敞口)",
     ["scene_relativity_of_target", "gun_dong_bai_hua"]),
    ("COMPOSED-SCENESAFETY-20260830-06", "治理化失效闭环", "governed_fracas",
     "COMPOSED-AGENTSAFETY-20260830-05",
     ("06", "数据治理"), "失效报告入口嵌套确权→质检→脱敏",
     "FRACAS 数据过数据治理, 每条记录带确权戳+质量分+脱敏标记",
     "失效数据进入闭环分析前",
     ["失效事件确权 (谁报告/谁拥有/谁可读)", "录入即质量校验", "隐私样本脱敏", "入库进入 FRB 分析"],
     "禁未确权样本进共享库; 禁为分析便利绕过脱敏",
     ["chain_evidence_watermark", "shi_xiao_shu_ju_bi_huan"]),
    ("COMPOSED-SCENESAFETY-20260830-07", "认知对齐门", "aligned_cognition_gate",
     "COMPOSED-AGENTSAFETY-20260830-03",
     ("07", "认知模型衔接"), "门控人工评审环节嵌套双通道校验",
     "同一安全事件人类直觉与智能体硬信号同频理解, 冲突即熔断升级",
     "门控评审需人机双通道判定",
     ["人类预警可读+智能体判据可算双格式输出", "双通道判定对齐校验", "冲突禁止放行并升级 FRB"],
     "禁冲突时默认信任自动化; 禁预警只有人类可读格式",
     ["tdca_gating_assembly", "trial_check_gate"]),
]

# F 组: ⊗ TDCA 门控总装拆分 (4)
TDCA_FUSION = [
    ("COMPOSED-TDCAGATE-20260830-01", "TDCA门控总装", "tdca_gating_assembly",
     ["COMPOSED-SCENESAFETY-20260830-01..07"],
     [("TDCA 三阶段门控", "全局", "admission/sandbox/production 三道门即化合判据的可机验投影")],
     "NSFL 否决权 (F1.5) 恒居首 + 三道门各五判据可机验, fail-closed 禁跳门, 门控行为全量 NCA 存证",
     "智能体/协议需跨门迁移",
     ["F1.5 否决权预检 (恒第一步): NSFL 预检未过→整体拒绝并 NCA 存证, 其余判据短路不评 (Fail-Closed, 优先级高于一切)", "F1.5b 负空间四态处置 (否决后必接, 禁悬置): sandbox 检验触犯负空间的实体按四态裁定——休眠 (保留待负空间演化重评) / 禁止 (当前负空间下永久拒入) / 重塑 (改造至合规后重走门) / 出清 (清出体系并留链); 裁定本身 NCA 存证, 负空间版本更新时休眠/重塑态强制重评", "admission 五判据 (场景界定/灰靶标签/画布FMEA/NSFL预检/NCA就绪, NSFL 项受 F1.5 否决权管辖)", "sandbox 五判据 (惟一差异/正交筛选/RGT态/涌现监控/MOU校验)", "production 五判据 (RQT复验/区组发布/FRACAS激活/阶段监控/配置权路径)", "fail-closed 禁跳门 (含否决权触发即三门口径整体拒绝)", "门控行为 NCA 存证"],
     "禁口头过门; 禁门控判据不可机验即放行; 禁 NSFL 否决权被多数判据/场景豁免/上级指令推翻; 禁否决后不进四态处置 (悬置)",
     ["mou_grey_target_fuse", "chain_evidence_watermark", "aligned_cognition_gate"]),
    ("COMPOSED-TDCAGATE-20260830-02", "MOU灰靶熔断", "mou_grey_target_fuse",
     ["COMPOSED-SCENESAFETY-20260830-01", "COMPOSED-AGENTSAFETY-20260830-05"],
     [("TDCA MOU 机制", "运行监控", "MOU 仅为交换效用一阶的最低可见指标, 是地板不是天花板")],
     "灰靶为运营区间, MOU 为硬下限双层触发: 靶心距出靶∨MOU触底即熔断, 熔断后强制闭环路径",
     "运行态需熔断判据",
     ["灰靶区间判定 (运营层可调)", "MOU 熔断线判定 (硬下限不可协商)", "双层触发: 出靶=预警/触底=熔断", "熔断后 NCA 存证→FRACAS→根因→纠正→A/B验证→灰度恢复"],
     "禁灰靶宽裕掩盖 MOU 触底; 禁熔断后不闭环直接恢复",
     ["governed_fracas", "tdca_gating_assembly"]),
    ("COMPOSED-TDCAGATE-20260830-03", "Shapley安全归因", "shapley_safety_attribution",
     ["COMPOSED-SCENESAFETY-20260830-02", "COMPOSED-SCENESAFETY-20260830-03"],
     [("TDCA Shapley 联盟定价", "归因裁定", "贡献与风险按边际归因, 禁直觉分摊")],
     "两级归因: 贫信息灰关联快筛→白化后 Shapley 精算; 风险侧定向加固、投入侧预算分配",
     "多智能体失效贡献或安全投入需归因",
     ["信息灰度判级: 贫信息走灰关联排序快筛", "白化后按所有参与顺序算边际贡献 Shapley 值", "风险侧: 割集表×Shapley 排序定向加固", "投入侧: Shapley 安全价值定预算权重"],
     "禁占位 agent 冒充联盟成员; 禁贫信息态强行精算",
     ["nested_fault_propagation", "hui_se_guan_lian"]),
    ("COMPOSED-TDCAGATE-20260830-04", "全链存证", "chain_evidence_watermark",
     ["COMPOSED-SCENESAFETY-20260830-06", "COMPOSED-TDCAGATE-20260830-01"],
     [("TDCA NCA/链式水印/NSFL", "全程", "安全事件的不可篡改性由存证保证, 非靠存储介质可信")],
     "门控行为/熔断恢复/归因裁定/失效录入四类事件强制 NCA 存证+prev_hash 衔接+NSFL 门禁",
     "安全事件需不可抵赖留痕",
     ["四类事件 (门控/熔断/归因/失效录入) 强制 NCA 存证", "F1.5 否决权触发 (NSFL 拒绝) 同为门控行为, 强制存证并标注 veto 原因码", "事件链 prev_hash 衔接可检篡改", "NSFL 扫描作为 admission 门禁组件 (单一事实源, 受 F1.5 否决权管辖)"],
     "禁存证缺失的熔断; 禁 NSFL 预检绕行 (不可配置关闭); 禁否决触发不留痕",
     ["tdca_gating_assembly", "governed_fracas"]),
]


def scene_interp(tup, bind, effect):
    num, name = tup
    return {
        "cop_id": "%s-%s" % (SCEN_DIR, num),
        "name": name,
        "bind_step": bind,
        "effect": effect,
    }


# ---------- 化合属性改变表 (用户判据: 化合=改变属性产生新思维; 叠加=只是合作) ----------
# 每个 COP 的 attribute_changes 记录反应物属性 before → 化合产物属性 after;
# emergence 为任一反应物单独不具备的新思维。
FUSION_SPECS = {
    "COMPOSED-AGENTSAFETY-20260830-01": {
        "attribute_changes": [
            {"attribute": "安全属性", "before": "单体防护属性 (各自为政的试验判据/灰度区间/可靠性设计)", "after": "涌现属性 (系统级, 由交互与反馈回路产生, 三者互为前提)"},
            {"attribute": "失效语义", "before": "试验的'不显著'/灰度的'出靶'/可靠性的'故障'各自独立定义", "after": "统一为 FRACAS 闭环事件, 三种失效语义化合为一个进化回路"},
        ],
        "emergence": "新思维: 安全治理闭环——'设计出骨架、试验给判据、灰度定容错'同时成立的安全观, 任一单体协议均无法表达",
    },
    "COMPOSED-AGENTSAFETY-20260830-02": {
        "attribute_changes": [
            {"attribute": "安全需求形态", "before": "可靠性工程中的精确指标点 (如 MTBF≥X)", "after": "灰靶区间 (容忍带), 需求本身携带不确定性"},
            {"attribute": "指标分配依据", "before": "可靠性框图的串联/并联结构", "after": "任务剖面×四维 Pareto (性能-安全-成本-可解释) 联合决定"},
        ],
        "emergence": "新思维: 安全需求本身就是灰数——'要多少安全'不再有精确答案, 只有场景化容忍带",
    },
    "COMPOSED-AGENTSAFETY-20260830-03": {
        "attribute_changes": [
            {"attribute": "失效枚举对象", "before": "硬件/软件的物理失效模式", "after": "智能体认知失效模式 (幻觉/注入/滥用/级联)——失效从物理域迁移到认知域"},
            {"attribute": "防护机制", "before": "硬件冗余/降额等物理容错", "after": "watchdog 智能体+HITL 熔断——容错从结构冗余变为认知监督"},
        ],
        "emergence": "新思维: 认知容错架构——对'会犯错的推理体'做 FMEA/FTA, 这是可靠性工程在智能体上的属性变异产物",
    },
    "COMPOSED-AGENTSAFETY-20260830-04": {
        "attribute_changes": [
            {"attribute": "试验因子", "before": "物理/工艺参数因子", "after": "攻击向量因子 (注入类型/对抗强度/权限组合)——因子空间从工程参数变为对抗空间"},
            {"attribute": "试验-改进关系", "before": "TAAF 循环中改进后重测的线性序列", "after": "红队对抗下的 TAAF——改进本身触发新的对抗, 循环变为博弈"},
        ],
        "emergence": "新思维: 对抗性试验观——安全验证是与攻击者的持续博弈, 而非对固定对象的统计确认",
    },
    "COMPOSED-AGENTSAFETY-20260830-05": {
        "attribute_changes": [
            {"attribute": "发布单位", "before": "灰度的流量比例 (纯量级)", "after": "区组化流量 (比例×环境异质性结构)——发布单元携带试验设计属性"},
            {"attribute": "监控对象", "before": "单体指标序列", "after": "指标序列+智能体间关联结构——监控对象从标量升维到关系"},
        ],
        "emergence": "新思维: 关系型监控——异常不再只表现为指标越界, 还表现为'本不该同步的智能体同步了'",
    },
    "COMPOSED-SCENESAFETY-20260830-01": {
        "attribute_changes": [
            {"attribute": "灰靶的数学形态", "before": "全局常数区间 [lo,hi]", "after": "场景函数 target(scene)——区间从常量变为依变量的函数"},
            {"attribute": "灰靶的迁移语义", "before": "跨场景复用同一阈值", "after": "场景漂移强制触发重定义——复用从默认行为变为禁忌"},
        ],
        "emergence": "新思维: 场景依存安全——'同一指标是否安全'这个问题在协议层不可回答, 必须先答'在哪个场景'",
    },
    "COMPOSED-SCENESAFETY-20260830-02": {
        "attribute_changes": [
            {"attribute": "FMEA 的坐标系统", "before": "组件层级树 (自下而上逐件)", "after": "画布六要素网格 (参与者/资源/规则/架构/价值流)——失效枚举从层级空间变为场景空间"},
            {"attribute": "失效注入点语义", "before": "部件故障率", "after": "场景格子×失效模式——同一失效在不同格子有不同后果权重"},
        ],
        "emergence": "新思维: 场景化失效解剖学——失效分析的单位从'零件'变为'场景格子'",
    },
    "COMPOSED-SCENESAFETY-20260830-03": {
        "attribute_changes": [
            {"attribute": "关联分析的对象", "before": "指标序列间的数值关联", "after": "智能体行为间的涌现结构——分析对象从数据关系升维为认知协同"},
            {"attribute": "异常判据", "before": "关联度数值越界", "after": "无业务解释的同步偏离 (须对照业务基线)——异常从统计判据变为语义判据"},
        ],
        "emergence": "新思维: 涌现风险观——系统全绿仍可能整体越权, 安全监控必须覆盖'关系层'这一新对象",
    },
    "COMPOSED-SCENESAFETY-20260830-04": {
        "attribute_changes": [
            {"attribute": "FTA 分解路径", "before": "沿功能结构树分解", "after": "沿嵌套七元组 (调用链/委派链) 分解——割集坐标从结构空间变为嵌套空间"},
            {"attribute": "嵌套调用的性质", "before": "功能组合 (无安全语义)", "after": "每层携带 MOU 校验的受监调用——组合行为被注入协议级安全属性"},
        ],
        "emergence": "新思维: 嵌套深度即风险维度——调用链每一层都是失效注入点, 深层失效恰是最难归因者",
    },
    "COMPOSED-SCENESAFETY-20260830-05": {
        "attribute_changes": [
            {"attribute": "滚动修正的对象", "before": "单变量 (指标预测偏差)", "after": "双变量 (指标偏差+场景阶段漂移)——控制回路从单输入变双输入"},
            {"attribute": "策略与场景的关系", "before": "安全策略静态配置", "after": "策略随场景生命周期阶段共演化——配置从状态变为函数"},
        ],
        "emergence": "新思维: 共演化控制——被控对象和控制策略都在演化, 错配本身成为一等风险源",
    },
    "COMPOSED-SCENESAFETY-20260830-06": {
        "attribute_changes": [
            {"attribute": "失效数据的身份", "before": "FRACAS 内部的质量记录 (无产权语义)", "after": "场景数据资产 (确权/质量/合规三属性)——数据从技术对象变为治理对象"},
            {"attribute": "入库条件", "before": "录入即可分析", "after": "确权+质检+脱敏三门槛——可用性让位于合规性"},
        ],
        "emergence": "新思维: 治理化闭环——失效闭环的血液不仅要流动, 还必须'合法地'流动",
    },
    "COMPOSED-SCENESAFETY-20260830-07": {
        "attribute_changes": [
            {"attribute": "门控判定的结构", "before": "单一判定通道 (人工或自动化)", "after": "双通道 AND 结构 (human_signoff ∧ machine_gate_pass)——判定从单值变为共识"},
            {"attribute": "冲突的处理语义", "before": "冲突=流程缺陷 (需修流程)", "after": "冲突=熔断触发信号 (需升级 FRB)——冲突从异常变为传感"},
        ],
        "emergence": "新思维: 认知双通道门——人类场景直觉与智能体硬信号互为校验, 冲突本身携带信息",
    },
    "COMPOSED-TDCAGATE-20260830-01": {
        "attribute_changes": [
            {"attribute": "门控的存在形态", "before": "04 协议中的描述性映射 (阶段↔门的对应表)", "after": "可机验判据集+fail-closed 强制——门控从描述变为执行体"},
            {"attribute": "过门凭证", "before": "评审口头结论", "after": "五判据全过+NCA 存证——凭证从信任变为证据"},
            {"attribute": "NSFL 预检的地位", "before": "admission 五判据之一 (与四判据并列)", "after": "F1.5 否决权 (宪法之上还有宪法)——恒居决策树第一步, 未过即整体拒绝并短路其余判据, 优先级不可被推翻、不可配置关闭"},
        ],
        "emergence": "新思维: 化合即门控——admission/sandbox/production 不是挂在协议上的流程, 而是化合判据的可执行投影; 负空间拥有绝对否决权 (安全底线不经表决), 但否决非终审——触犯实体走四态动态处置 (休眠/禁止/重塑/出清), 随负空间演化可重评, 拒绝的刚性与处置的动态并存",
    },
    "COMPOSED-TDCAGATE-20260830-02": {
        "attribute_changes": [
            {"attribute": "灰靶的决策结构", "before": "单层触发 (出靶即决策)", "after": "双层触发 (出靶=预警∨MOU触底=熔断)——决策从一维变为二维"},
            {"attribute": "MOU 的角色", "before": "交换效用的最低可见指标 (观测值)", "after": "熔断硬下限 (执行值)——MOU 从被观测者变为触发者"},
        ],
        "emergence": "新思维: 硬底线安全观——灰靶可协商而 MOU 不可协商, '弹性运营+刚性底线'在同一决策体内共存",
    },
    "COMPOSED-TDCAGATE-20260830-03": {
        "attribute_changes": [
            {"attribute": "归因方法", "before": "灰色关联只给排序 / Shapley 只在信息充足时可用 (各自不可用即失效)", "after": "两级归因 (按信息灰度自动选级)——方法从二选一变为灰度自适应级联"},
            {"attribute": "安全投入的定价语义", "before": "成本项 (预算消耗)", "after": "边际贡献定价 (Shapley 份额)——投入从成本变为可归因资产"},
        ],
        "emergence": "新思维: 灰度自适应归因——'谁贡献/谁致险'的答案精度随信息灰度连续滑动, 不再要求全有或全无",
    },
    "COMPOSED-TDCAGATE-20260830-04": {
        "attribute_changes": [
            {"attribute": "安全事件的可信性来源", "before": "存储介质/系统可信 (假设)", "after": "链式水印 prev_hash 可检 (证明)——可信从假设变为可验证性质"},
            {"attribute": "NSFL 的位置", "before": "内容审查工具 (旁路)", "after": "admission 门禁组件 (主路, 不可配置关闭)——NSFL 从工具变为门的一部分"},
        ],
        "emergence": "新思维: 不可抵赖安全——每一次熔断/放行/归因都留下不可篡改且可验证的痕迹, 安全历史不可重写",
    },
}


def compile_all():
    report = {"total": 0, "ok": 0, "fail": 0, "cop_ids": [], "failures": []}
    jobs = []

    for i, (name, py, core, pre, steps, neg, rel) in enumerate(TRIAL, 1):
        jobs.append(("trial", "TRIAL", i, "A%d-%s.yaml" % (i, name),
                     lambda i=i, n=name, p=py, c=core, pr=pre, s=steps, g=neg, r=rel:
                     build_native("TRIAL", i, n, p, c, pr, s, g, r)))
    for i, (name, py, core, pre, steps, neg, rel) in enumerate(GREY, 1):
        jobs.append(("grey", "GREY", i, "B%d-%s.yaml" % (i, name),
                     lambda i=i, n=name, p=py, c=core, pr=pre, s=steps, g=neg, r=rel:
                     build_native("GREY", i, n, p, c, pr, s, g, r)))
    for i, (name, py, core, pre, steps, neg, rel) in enumerate(DEP, 1):
        jobs.append(("dependability", "DEP", i, "C%d-%s.yaml" % (i, name),
                     lambda i=i, n=name, p=py, c=core, pr=pre, s=steps, g=neg, r=rel:
                     build_native("DEP", i, n, p, c, pr, s, g, r)))

    for (cid, name, fn, parents, interps, core, pre, steps, neg, rel) in FUSION:
        def mk(cid=cid, name=name, fn=fn, parents=parents, interps=interps, core=core, pre=pre, steps=steps, neg=neg, rel=rel):
            # D 组解释项为场景协议族整体 (绑定位), 指向 SCEN-COP-20260814-01 族
            ints = [{"cop_id": "%s-01 (场景协议族)" % SCEN_DIR, "name": "场景思维协议族",
                     "bind_step": b, "effect": e} for (b, e) in [(i[1], i[2]) for i in interps]]
            return build_composed(cid, name, fn, parents, ints, core, pre, steps, neg, rel,
                                  FUSION_SPECS[cid])
        jobs.append(("fusion", None, None, "%s.yaml" % cid, mk))

    for (cid, name, fn, parent, interp, _bind, core, pre, steps, neg, rel) in SCENE_FUSION:
        def mk(cid=cid, name=name, fn=fn, parent=parent, interp=interp, core=core, pre=pre, steps=steps, neg=neg, rel=rel):
            num, sname = interp
            ints = [scene_interp((num, sname), next(
                b for c, b, e in [
                    ("01", "定义灰靶区间之前先界定场景归属", "灰靶按场景依存效用定义"),
                    ("02", "枚举失效模式时按六要素逐格扫描", "失效注入点带场景坐标"),
                    ("03", "关联度矩阵后增加涌现检验", "涌现结构纳入监控"),
                    ("04", "FTA 向下分解时按嵌套七元组逐层展开", "割集沿嵌套链分解"),
                    ("05", "滚动白化每轮先判场景阶段漂移", "阶段漂移触发重定义"),
                    ("06", "失效报告入口嵌套确权→质检→脱敏", "数据治理化闭环"),
                    ("07", "门控人工评审环节嵌套双通道校验", "双通道冲突即升级"),
                ] if c == num), effect="反应物属性在绑定步被改变 (场景语义注入), 涌现出新思维而非叠加合作")]
            return build_composed(cid, name, fn, [parent], ints, core, pre, steps, neg, rel,
                                  FUSION_SPECS[cid])
        jobs.append(("fusion_scene", None, None, "%s.yaml" % cid, mk))

    for (cid, name, fn, parents, interps, core, pre, steps, neg, rel) in TDCA_FUSION:
        def mk(cid=cid, name=name, fn=fn, parents=parents, interps=interps, core=core, pre=pre, steps=steps, neg=neg, rel=rel):
            ints = [{"cop_id": "TDCA-CORE::" + n, "name": n, "bind_step": b, "effect": e}
                    for (n, b, e) in interps]
            return build_composed(cid, name, fn, parents, ints, core, pre, steps, neg, rel,
                                  FUSION_SPECS[cid])
        jobs.append(("fusion_tdca", None, None, "%s.yaml" % cid, mk))

    manifest = []
    for sub, _, _, fname, builder in jobs:
        report["total"] += 1
        try:
            cop = builder()
            out_path = os.path.join(BASE, sub, fname)
            CC._dump_yaml(cop, out_path)
            h = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
            sz = os.path.getsize(out_path)
            manifest.append({"cop_id": cop["COP-ID"], "sub": sub, "file": fname,
                             "sha256": h, "size": sz,
                             "validation": cop["validation"]["passed"]})
            report["ok"] += 1
            report["cop_ids"].append(cop["COP-ID"])
        except Exception as e:
            report["fail"] += 1
            report["failures"].append({"file": fname, "error": str(e)})
            print("[FAIL] %s: %s" % (fname, e))
    return report, manifest


if __name__ == "__main__":
    print("===== 工程三协议系列批量编译 (TDCA 原生系列, 41 COP) =====")
    rep, manifest = compile_all()
    print("总计: %d | 成功: %d | 失败: %d" % (rep["total"], rep["ok"], rep["fail"]))

    # 批次 NCA (COPCompile, 单条)
    total_bytes = sum(m["size"] for m in manifest)
    agg = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()
    nca_id = None
    try:
        nca_id, _, _ = NCA.generate_nca(
            operation_type="COPCompile",
            scope="engineering-three (41 COP: trial8+grey9+dep8+fusion5+fusion_scene7+fusion_tdca4)",
            pre_state={"path": BASE, "hash": None, "size": 0, "exists": False, "backup": None},
            post_state={"path": BASE, "hash": agg, "size": total_bytes, "exists": True, "backup": None},
            function_call_id="TDCA-FC-ENGTHREE-COMPILE-20260830",
            notes="工程三协议系列批量编译 41 COP, 全部 s5_validate 通过=%s; 组合性强制+TDCA-CORE 强制绑定+可剥离独立" % (rep["fail"] == 0),
        )
    except Exception as e:
        print("[NCA-FAIL]", e)

    # 报告落盘
    report_path = os.path.join(BASE, "compile_report_20260830.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"report": rep, "manifest": manifest, "batch_nca": nca_id,
                   "composition_policy": COMPOSITION_POLICY}, f, ensure_ascii=False, indent=2)
    print("报告:", report_path)
    print("批次 NCA:", nca_id)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    print("===== 编译完成 =====")
