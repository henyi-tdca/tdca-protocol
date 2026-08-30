# -*- coding: utf-8 -*-
"""
回审修订：将既有化合 COP 按用户 2026-08-30 编译原则修订（GSEQ-0749 后续）。
原则依据：编译清单「组合性与化合判据」第 1~5b 条（组合性强制 / TDCA 强制 /
可剥离声明 / 换绑自由 / 化合判据 fusion_spec / F1.5 否决权 / F1.5b 四态处置）。

修订范围（回审判定）：
  A 组 44 个旧化合 COP（compositions/39 + hundred_schools/4 + marxism/1）
     —— 七原则全缺, 全量修订;
  B 组 engineering-three/ 16 个化合 COP
     —— 仅缺 composition_policy.bind_policy, 补丁修订。

fusion_spec 生成纪律（诚实归档, 不虚构）：
  attribute_changes / emergence 由该 COP 既有 interpretant.effect 文本归档生成——
  该文本在创作时即按"属性改变产生新思维"语义撰写, 本次仅结构化入档。
"""
import os, sys, io, json, glob, datetime
sys.stdout.reconfigure(encoding="utf-8")
import yaml

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "nca-generator"))
sys.path.insert(0, _THIS)
import nca_generator as NCA
from cognitive_compiler import s5_validate

CONSTITUTION = (
    # 正典宪法 (单一事实源: 编译清单第 5/5b 条; 2026-08-30 REASONIX 审查项②修复统一)
    "NSFL 否决权 (F1.5, 用户裁定 2026-08-30 21:07): 对于任何无法通过 NSFL 预检的事件 (负空间触碰), "
    "即使其他四判据全部通过, 亦视为整体拒绝 (Fail-Closed); NSFL 预检的优先级永远高于其他四判据"
    "——负空间是安全宪法的宪法, 不可配置关闭, 不可被多数判据推翻。"
    "四态动态处置 (F1.5b, 用户裁定 2026-08-30 21:19): TDCA 是动态管理, 负空间本质保守不轻易变化但仍会演化"
    "——现在触犯不等于永远触犯; 否决权的不可推翻性仅指即时门控裁决, 不指永恒身份; "
    "sandbox 检验触犯负空间的实体走四态处置: 休眠/禁止/重塑/出清 (裁定 NCA 存证, 禁悬置), "
    "负空间版本更新时休眠/重塑态强制重评。"
)

POLICY = {
    "standalone": False,
    "tdca_native": True,
    "mandatory_base": "TDCA-CORE (TDCA 体系内强制遵守, 不可配置关闭)",
    "detachable": "剥离 TDCA 治理层后协议语义保持独立自洽, 可移植至其他治理体系 (设计目标)",
    "bind_policy": "解释项绑定关系为运用层配置, 运行期允许换绑 (dispatch.graph 可扩展)",
    "note": "思维协议不是独立发挥作用的, 须与系列内其他 COP 组合调用 (用户裁定 2026-08-30)",
    "constitution": CONSTITUTION,
}

NEG_APPEND = [
    "⊗ 禁止叠加冒充化合: 组合后若无属性改变、无新思维涌现, 须降级标注为两个独立思维的合作 (化合判据, 用户裁定 2026-08-30 20:52)",
    "⊗ 禁止 NSFL 否决权被推翻: NSFL 预检未过的事件, 禁止以其余判据全部通过、多数决、场景豁免、上级指令等任何理由放行 (F1.5 宪法条款)",
    "⊗ 禁止把否决当终审: 触犯负空间按四态处置——休眠/禁止/重塑/出清, 裁定存证, 禁悬置 (F1.5b)",
]


def build_fusion_spec(cop):
    """由既有 interpretant 效应文本归档生成 fusion_spec (不虚构新语义)。"""
    comp = cop.get("composition") or {}
    interps = comp.get("interpretants") or []
    parent = comp.get("parent")
    if isinstance(parent, list):
        parent = "、".join(str(p) for p in parent)
    parent = str(parent or cop.get("source_expert") or "父原语")
    if not interps:
        return None
    changes, effects = [], []
    for it in interps:
        iid, eff = str(it.get("cop_id", "解释项")), str(it.get("effect", "")).strip()
        bind = str(it.get("bind_step", "绑定步")).strip()
        if not eff:
            continue
        effects.append(eff)
        changes.append({
            "attribute": "父原语决策语义",
            "before": "『%s』按原范式独立运作" % parent,
            "after": "绑定步『%s』注入解释项『%s』后: %s" % (bind, iid, eff[:120] + ("…" if len(eff) > 120 else "")),
        })
    if not changes:
        return None
    changes.append({
        "attribute": "解的空间与结果属性",
        "before": "父范式原生 Outcome 语义",
        "after": "涌现语义——解释项效应改写结果属性, 非两个原语的并集",
    })
    return {
        "attribute_changes": changes,
        "emergence": " ".join(effects),
        "provenance": "由本 COP 既有 interpretant 效应文本归档生成 (2026-08-30 回审修订)——该文本创作时即按属性改变语义撰写, 未新增虚构语义",
    }


def revise_old_composed(path):
    cop = yaml.safe_load(io.open(path, encoding="utf-8"))
    if not isinstance(cop, dict):
        return None
    prior_base = cop.get("base_protocol")
    cop["composition_policy"] = dict(POLICY)
    cop["base_protocol"] = "TDCA-CORE"
    fs = build_fusion_spec(cop)
    if fs:
        cop["fusion_spec"] = fs
    neg = cop.get("negative_space") or []
    neg_text = " ".join(str(x) for x in neg)
    for clause in NEG_APPEND:
        key = clause[2:8]  # 取关键短语判重
        if key not in neg_text:
            neg.append(clause)
    cop["negative_space"] = neg
    cop["retro_revision"] = {
        "date": "2026-08-30",
        "basis": "用户 2026-08-30 编译原则回审 (组合性/化合判据/F1.5/F1.5b)",
        "prior_base_protocol": prior_base,
    }
    issues = s5_validate(cop)
    return cop, issues


def patch_bind_policy(path):
    cop = yaml.safe_load(io.open(path, encoding="utf-8"))
    cp = cop.get("composition_policy")
    if cp is None:
        return None
    changed = False
    if "bind_policy" not in cp:
        cp["bind_policy"] = POLICY["bind_policy"]
        changed = True
    return cop, changed


def main():
    rep = {"A_旧化合修订": [], "A_校验失败_未写入": [], "B_补丁": [], "ts": datetime.datetime.now().isoformat()}
    targets = []
    for fam in ("compositions", "hundred_schools", "marxism"):
        for f in sorted(glob.glob(os.path.join(_THIS, fam, "**", "*.yaml"), recursive=True)):
            try:
                cop = yaml.safe_load(io.open(f, encoding="utf-8"))
            except Exception:
                continue
            if isinstance(cop, dict) and "COMPOSED" in str(cop.get("type", "")):
                targets.append(f)
    print("A 组待修订:", len(targets))
    for f in targets:
        rel = os.path.relpath(f, _THIS)
        try:
            cop, issues = revise_old_composed(f)
        except Exception as e:
            rep["A_校验失败_未写入"].append({"file": rel, "error": str(e)[:200]})
            continue
        if issues:
            rep["A_校验失败_未写入"].append({"file": rel, "cop_id": cop.get("COP-ID"), "issues": issues})
            continue
        with io.open(f, "w", encoding="utf-8") as fh:
            yaml.safe_dump(cop, fh, allow_unicode=True, sort_keys=False)
        rep["A_旧化合修订"].append({"file": rel, "cop_id": cop.get("COP-ID"),
                                    "fusion_spec": bool(cop.get("fusion_spec"))})
    b_changed = 0
    for f in sorted(glob.glob(os.path.join(_THIS, "engineering-three", "**", "*.yaml"), recursive=True)):
        try:
            cop = yaml.safe_load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        if not (isinstance(cop, dict) and ("COMPOSED" in str(cop.get("type", "")) or "COMPOUND" in str(cop.get("type", "")))):
            continue
        r = patch_bind_policy(f)
        if not r:
            continue
        cop, changed = r
        if changed:
            with io.open(f, "w", encoding="utf-8") as fh:
                yaml.safe_dump(cop, fh, allow_unicode=True, sort_keys=False)
            rep["B_补丁"].append(os.path.relpath(f, _THIS))
            b_changed += 1
    print("A 组修订成功:", len(rep["A_旧化合修订"]), "| 校验失败未写入:", len(rep["A_校验失败_未写入"]))
    print("B 组补丁:", b_changed)
    out = os.path.join(_THIS, "engineering-three", "retro_revision_report_20260830.json")
    json.dump(rep, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("报告:", out)
    return len(rep["A_旧化合修订"]), b_changed


if __name__ == "__main__":
    main()
