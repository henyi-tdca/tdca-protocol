# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""三十六计思维协议编译器 (应用层)
依据: 思维协议编译器规范 (T1 五阶段流水线 + T2 类型系统 + 麦肯锡 COP schema 范本)
来源: TDCA-MEMO-006-Workspace 编译器开发阶段产物
任务: 将三十六计逐计编译为独立可执行思维协议 COP, 每计单独交付
复用: cognitive_compiler.s5_validate / _dump_yaml ; nca_generator.generate_nca
编码安全: 全中文经 Python open(encoding='utf-8') 写入, 遵守 NSFL R2
"""
import os
import sys
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
STRATAGEMS_DIR = os.path.join(_THIS, "stratagems")
ensure_dirs()
os.makedirs(STRATAGEMS_DIR, exist_ok=True)

# ---------- 三十六计知识库 (6 套 x 6 计) ----------
STRATAGEMS = [
    ("胜战计", 1, "瞒天过海", "man_tian_guo_hai", "示假隐真, 于常态中隐蔽异动",
     "己方关键行动需隐蔽, 敌方习以为常而放松警惕",
     ["制造日常假象使敌不疑", "将关键行动嵌入常规流程", "待敌懈怠则突发"],
     "敌方高度戒备或已识破伪装则失效; 忌重复同一伪装"),
    ("胜战计", 2, "围魏救赵", "wei_wei_jiu_zhao", "攻敌必救, 避实击虚以解困",
     "盟友或己方被围, 正面难以直解",
     ["识别敌之要害与必救之处", "攻其必救迫使敌回援", "于敌回援途中设伏歼之"],
     "敌无必救之处或无回援动机则失效"),
    ("胜战计", 3, "借刀杀人", "jie_dao_sha_ren", "假手他人除患, 己不亲沾",
     "需除去对手但不宜亲为",
     ["识别可借之力(第三方矛盾)", "诱发其动手", "坐收其利控风险"],
     "借力对象反噬或识破则反噬己; 忌无第三方矛盾强行借"),
    ("胜战计", 4, "以逸待劳", "yi_yi_dai_lao", "养精蓄锐, 待敌疲而击之",
     "敌远来或躁动, 己方可守",
     ["固守蓄力", "诱敌耗散", "敌疲则突击"],
     "己亦疲或时间不在己则不可行"),
    ("胜战计", 5, "趁火打劫", "chen_huo_da_jie", "乘敌之危, 速取可图之利",
     "敌内部生乱或受损",
     ["监视敌危", "速取可图之利", "控制反噬风险"],
     "敌危为假象(诱敌)则中伏"),
    ("胜战计", 6, "声东击西", "sheng_dong_ji_xi", "佯攻一侧, 实取另一侧",
     "敌注意力集中于某一处",
     ["示攻东面", "实备西面", "敌移则西取"],
     "敌方将多谋识破则反被调"),
    ("敌战计", 7, "无中生有", "wu_zhong_sheng_you", "由虚变实, 欺诈最终成真",
     "需造势而无可据之实",
     ["先示虚(小假使敌习)", "敌习以为常", "突转为实击之"],
     "虚实质变须连贯, 中段断则露馅; 忌对多疑之敌"),
    ("敌战计", 8, "暗度陈仓", "an_du_chen_cang", "明修栈道暗度陈仓, 佯动实奇袭",
     "需转移或突袭而正面被盯",
     ["明修显而易见的动作", "暗备真实路径", "暗径达成目标"],
     "佯动不真则敌不惑"),
    ("敌战计", 9, "隔岸观火", "ge_an_guan_huo", "坐视敌内斗, 待其自溃",
     "敌方营内讧, 己不宜介入",
     ["不介入", "观其互斗", "敌弱则取"],
     "敌可能联合对外则误判"),
    ("敌战计", 10, "笑里藏刀", "xiao_li_cang_dao", "示好怀刃, 缓兵而图之",
     "需近敌而备攻",
     ["示亲和", "懈敌备", "寻机下手"],
     "敌亦伪善则互藏刀, 险"),
    ("敌战计", 11, "李代桃僵", "li_dai_tao_jiang", "舍次保主, 以代价换大局",
     "两害须择其一",
     ["评估主次", "弃次要保关键", "控制损失"],
     "主次误判则舍主保次"),
    ("敌战计", 12, "顺手牵羊", "shun_shou_qian_yang", "微利必得, 伺隙取小",
     "行军或行动中见小利可图且无险",
     ["保持侦察", "见隙即取小利", "不恋战"],
     "小利诱深陷则因小失大"),
    ("攻战计", 13, "打草惊蛇", "da_cao_jing_she", "试探引动, 察敌虚实",
     "敌情不明",
     ["轻触试探", "观敌反应", "据反应定策"],
     "己亦需隐蔽时不宜惊蛇"),
    ("攻战计", 14, "借尸还魂", "jie_shi_huan_hun", "借无用或旧壳载新魂",
     "需借已有形式立新内容",
     ["觅可用之壳(名义/平台)", "注入新实质", "立稳"],
     "壳无号召力则空"),
    ("攻战计", 15, "调虎离山", "diao_hu_li_shan", "诱敌离其有利地形",
     "敌凭险固守",
     ["设饵诱离", "敌离则攻其失险", "歼之"],
     "敌识饵不理则徒劳"),
    ("攻战计", 16, "欲擒故纵", "yu_qin_gu_zong", "纵而再擒, 服其心志",
     "敌可擒但擒而易叛或逃",
     ["纵其小败", "懈其志", "确无逃路时擒"],
     "纵而失控则纵虎归山"),
    ("攻战计", 17, "抛砖引玉", "pao_zhuan_yin_yu", "以小引大, 示劣诱优",
     "欲获高价值反馈或资源",
     ["示小利或粗品", "诱对方出大招", "取其精"],
     "砖不真则引不出玉"),
    ("攻战计", 18, "擒贼擒王", "qin_zei_qin_wang", "击其要害首脑, 乱其全局",
     "敌体系依赖核心",
     ["识王(核心)", "直取", "余众自乱"],
     "王非真核或为替身则无效"),
    ("混战计", 19, "釜底抽薪", "fu_di_chou_xin", "断根绝源, 消敌势能",
     "敌势盛但其根基有隙",
     ["找敌能量源(补给/士气/关键依赖)", "断之", "敌势溃"],
     "薪非真源则抽空"),
    ("混战计", 20, "浑水摸鱼", "hun_shui_mo_yu", "乱中取利",
     "局混乱敌我难分",
     ["搅或乘乱", "于混沌中取利", "速清"],
     "己亦陷浑则自乱"),
    ("混战计", 21, "金蝉脱壳", "jin_chan_tuo_ke", "留形走实, 金蝉脱壳",
     "需撤离而不可显退",
     ["留置伪装(形)", "实转移", "形存实去"],
     "伪装不似则早识"),
    ("混战计", 22, "关门捉贼", "guan_men_zhuo_zei", "围闭聚歼, 不使逸走",
     "小股之敌可围",
     ["设围(门)", "诱入", "闭门歼之"],
     "门不密则贼逸; 对大敌不宜"),
    ("混战计", 23, "远交近攻", "yuan_jiao_jin_gong", "交远制近, 分化削邻",
     "多敌环伺需逐个破",
     ["交好远敌使其不援", "专攻近敌", "破一近再移"],
     "远敌亦图近则反被夹"),
    ("混战计", 24, "假道伐虢", "jia_dao_fa_guo", "借路实取, 假途灭虢",
     "需过第三国境以攻敌",
     ["请借道(示不害)", "过道即取道主", "再攻原敌"],
     "道主识破则拒或反"),
    ("并战计", 25, "偷梁换柱", "tou_liang_huan_zhu", "暗易其构, 夺其主控",
     "敌结构可依",
     ["识梁(关键结构)", "暗换", "敌构变己控"],
     "换显则敌觉复"),
    ("并战计", 26, "指桑骂槐", "zhi_sang_ma_huai", "敲侧警正, 以威慑众",
     "需警诫不从者",
     ["指桑(旁)示威", "骂槐(正)惧", "众服"],
     "桑槐皆不畏则无效"),
    ("并战计", 27, "假痴不癫", "jia_chi_bu_dian", "佯愚藏智, 免疑待机",
     "势弱需避嫌",
     ["示痴(无争)", "内蓄其实", "机至则发"],
     "痴过真则失机"),
    ("并战计", 28, "上屋抽梯", "shang_wu_chou_ti", "置敌绝地, 断其归路",
     "诱敌深入",
     ["设梯诱登", "敌上则抽梯", "敌困"],
     "梯抽早则敌不登"),
    ("并战计", 29, "树上开花", "shu_shang_kai_hua", "虚张声势, 借势壮己",
     "力弱需威慑",
     ["借他物(盟/势)饰己", "张声势", "敌疑不敢动"],
     "势虚被戳则崩"),
    ("并战计", 30, "反客为主", "fan_ke_wei_zhu", "渐进夺主, 客变主位",
     "己处客位而可逆",
     ["先为客立脚跟", "渐进掌要", "夺主位"],
     "主防客则逆"),
    ("败战计", 31, "美人计", "mei_ren_ji", "以欲诱心, 乱其志断",
     "敌将刚而好色或有明显之欲",
     ["投其所好(美人)", "乱其断", "乘隙取"],
     "敌无此欲或识破则反制"),
    ("败战计", 32, "空城计", "kong_cheng_ji", "虚而示虚, 疑兵退敌",
     "兵少敌众, 不可战",
     ["示空(无备)", "敌疑有伏", "退"],
     "敌将果断或识破则入城"),
    ("败战计", 33, "反间计", "fan_jian_ji", "离间敌谋, 使其自疑",
     "敌有谋臣可用间",
     ["识可间者", "施伪情", "敌疑而自乱"],
     "敌将明则间不行"),
    ("败战计", 34, "苦肉计", "ku_rou_ji", "自伤取信, 间入敌腹",
     "需深入敌内",
     ["自伤(苦)取敌信", "入敌", "为内应"],
     "伤不真或敌不信则败露"),
    ("败战计", 35, "连环计", "lian_huan_ji", "多计勾连, 环环相扣",
     "单计不足成事",
     ["设多计相生", "一发动全", "敌应接不暇"],
     "一环破则连锁崩"),
    ("败战计", 36, "走为上", "zou_wei_shang", "势不可为则退, 存为根本",
     "必败不可战",
     ["识不可为", "全师而退", "保根本待机"],
     "可战而走则失机; 非怯战是知止"),
]


def assemble_one(stratum, idx, name, pinyin, core, scene, steps, neg):
    """S2-S4: 将单计编译为 COP (对齐麦肯锡 COP schema)"""
    fn_name = pinyin
    primitive = {
        "name": fn_name,
        "method": name,
        "signature": "fn %s(context: Situation) -> Outcome" % fn_name,
        "precond": scene,
        "postcond": core + " (目标达成)",
        "negative_space": "⊗ " + neg,
        "steps": steps,
        "nca_emit": True,
    }
    cop = {
        "COP-ID": "STRATAGEM-COP-20260814-%02d" % idx,
        "source_expert": "thirty_six_stratagems",
        "compiler": "cognitive_compiler (T1+T2 规范复用)",
        "compiled_at": datetime.datetime.now().isoformat(),
        "stratum": stratum,
        "soul": {
            "identity": name,
            "core": core,
            "role": "思维协议 (兵法策略类)",
            "category": "三十六计 / " + stratum,
        },
        "primitives": [primitive],
        "dispatch": {
            "main_pipeline": fn_name,
            "graph": [{"from": fn_name, "to": []}],
            "note": "单计独立协议, 主原语 %s 即该计执行体" % fn_name,
        },
        "decision": [
            {"if": scene, "call": fn_name},
        ],
        "skills": [],
        "negative_space": [
            "⊗ " + neg,
            "⊗ 禁止机械套用: 计须契合态势, 非态势则不用",
            "⊗ 禁止违反 NSFL: 伦理/法律负空间不可越",
        ],
        "nsfl_version": NSFL_VERSION,
    }
    CC.s5_validate(cop)
    return cop, fn_name


def compile_all():
    report = {"total": len(STRATAGEMS), "ok": 0, "fail": 0, "cop_ids": [], "nca_ids": []}
    for stratum, idx, name, pinyin, core, scene, steps, neg in STRATAGEMS:
        try:
            cop, fn_name = assemble_one(stratum, idx, name, pinyin, core, scene, steps, neg)
            fname = "第%02d计-%s.yaml" % (idx, name)
            out_path = os.path.join(STRATAGEMS_DIR, fname)
            CC._dump_yaml(cop, out_path)
            h = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
            sz = os.path.getsize(out_path)
            nid, _, _ = NCA.generate_nca(
                operation_type="CodeGen",
                scope=".tdca-protocol/cognitive-compiler/stratagems (第%02d计-%s COP)" % (idx, name),
                pre_state={"path": out_path, "hash": None, "size": 0, "exists": False, "backup": None},
                post_state={"path": out_path, "hash": h, "size": sz, "exists": True, "backup": None},
                function_call_id="TDCA-FC-STRATAGEM-%02d" % idx,
                notes="三十六计第%d计 %s 编译为 COP, 验证=%s" % (idx, name, cop["validation"]["passed"]),
            )
            report["ok"] += 1
            report["cop_ids"].append(cop["COP-ID"])
            report["nca_ids"].append(nid)
        except Exception as e:
            report["fail"] += 1
            print("[FAIL] 第%02d计-%s: %s" % (idx, name, e))
    return report


if __name__ == "__main__":
    print("===== 三十六计思维协议编译 (混元接管, MEMO-006 规范) =====")
    rep = compile_all()
    print("总计: %d | 成功: %d | 失败: %d" % (rep["total"], rep["ok"], rep["fail"]))
    print("COP 目录: %s" % STRATAGEMS_DIR)
    print("NCA 总数(全工作区): %d" % len(NCA.list_ncas()))
    print("前 3 计 COP-ID:", rep["cop_ids"][:3])
    print("末计 COP-ID:", rep["cop_ids"][-1])
    print("===== 编译完成 =====")
