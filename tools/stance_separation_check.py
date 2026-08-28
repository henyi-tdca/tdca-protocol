# -*- coding: utf-8 -*-
"""立场分离校验器 (GSEQ-0601 · 编译器强制门)
三律规则化:
  R1 原语禁立场字段: primitives 与根节点不得携带 stance/立场 字段 (立场字段只允许出现在 scene_binding.bindings[*])
  R2 立场经 scene_binding 注入: 任何立场声明必须位于 scene_binding.bindings[*], 且每条绑定含 scene+stance
  R3 挂载强制: 携带 scene_binding 的 COP 必须声明 mounts 四类依赖: scene/knowledge_graph/skill/contract (律三)
  R4 fail-closed: 任何违规抛 StanceViolation (编译即熔断, 不落盘)

执行策略: s5_validate 末尾自动调用 check_cop(strict=True);
  旧 COP(无 scene_binding/mounts)天然通过 —— R1/R2 仅在有立场字段时触发, R3 仅在携带 scene_binding 时触发。
"""
KEYWORD_STANCE_FIELDS = {"stance", "立场"}
BINDING_REQUIRED = {"scene", "stance"}
MOUNTS_REQUIRED = {"scene", "knowledge_graph", "skill", "contract"}


class StanceViolation(Exception):
    """立场分离违规 (fail-closed, 编译熔断)"""
    pass


def _find_stance_fields(obj, path="", out=None):
    if out is None:
        out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = "%s.%s" % (path, k) if path else str(k)
            if str(k).lower() in KEYWORD_STANCE_FIELDS and "scene_binding" not in p:
                out.append(p)
            _find_stance_fields(v, p, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _find_stance_fields(v, "%s[%d]" % (path, i), out)
    return out


def check_cop(cop, strict=True):
    """返回 issues 列表; strict=True 时抛 StanceViolation (fail-closed)"""
    issues = []
    if not isinstance(cop, dict):
        return issues
    # R1 原语禁立场字段
    for pr in cop.get("primitives") or []:
        if isinstance(pr, dict):
            for k in pr:
                if str(k).lower() in KEYWORD_STANCE_FIELDS:
                    issues.append("R1 违规: primitives[%s] 携带立场字段 '%s'" % (pr.get("name"), k))
    # R1b 根节点(非 scene_binding 路径)立场字段
    for k in cop:
        if str(k).lower() in KEYWORD_STANCE_FIELDS:
            issues.append("R1 违规: 根节点携带立场字段 '%s' (立场只允许在 scene_binding)" % k)
    # R2 立场必须经 scene_binding.bindings 注入
    sb = cop.get("scene_binding")
    if sb is not None:
        if not isinstance(sb, dict) or not isinstance(sb.get("bindings"), list) or not sb["bindings"]:
            issues.append("R2 违规: scene_binding 缺 bindings 列表")
        else:
            for i, b in enumerate(sb["bindings"]):
                if not isinstance(b, dict):
                    issues.append("R2 违规: bindings[%d] 非字典" % i)
                    continue
                missing = BINDING_REQUIRED - set(b)
                if missing:
                    issues.append("R2 违规: bindings[%d] 缺 %s" % (i, sorted(missing)))
    # R3 挂载强制 (携带 scene_binding 的 COP 必须四类挂载齐备)
    if sb is not None:
        mounts = cop.get("mounts")
        if not isinstance(mounts, dict):
            issues.append("R3 违规: 携带 scene_binding 的 COP 缺 mounts 块 (四类依赖: %s)" % sorted(MOUNTS_REQUIRED))
        else:
            missing = MOUNTS_REQUIRED - set(mounts)
            if missing:
                issues.append("R3 违规: mounts 缺 %s" % sorted(missing))
    # R5 律三v2 动态状态通道: 声明状态依赖的 COP 须挂 data_feed; data_feed 结构须完备
    if cop.get("state_dependent") is True:
        mounts = cop.get("mounts") or {}
        df = mounts.get("data_feed")
        if not isinstance(df, dict):
            issues.append("R5a 违规: state_dependent=true 但 mounts.data_feed 缺失 (动态状态通道未挂载)")
        else:
            issues.extend(check_data_feed(df))
    elif isinstance(cop.get("mounts"), dict) and "data_feed" in cop["mounts"]:
        # 未声明 state_dependent 但挂了 data_feed → 仍校验结构
        issues.extend(check_data_feed(cop["mounts"]["data_feed"]))
    if strict and issues:
        raise StanceViolation("; ".join(issues))
    return issues


def check_data_feed(df):
    """data_feed 结构校验: source 非空 / variables 非空 / freshness_sla.max_staleness_s>0"""
    issues = []
    if not df.get("source"):
        issues.append("R5b 违规: data_feed 缺 source (数据源标识)")
    variables = df.get("variables")
    if not isinstance(variables, list) or not variables:
        issues.append("R5b 违规: data_feed 缺 variables (决策状态变量清单)")
    else:
        for i, v in enumerate(variables):
            name = v.get("name") if isinstance(v, dict) else v
            if not name:
                issues.append("R5b 违规: variables[%d] 缺变量名" % i)
    sla = df.get("freshness_sla")
    if not isinstance(sla, dict) or not isinstance(sla.get("max_staleness_s"), (int, float)) or sla.get("max_staleness_s") <= 0:
        issues.append("R5b 违规: data_feed.freshness_sla.max_staleness_s 须为正数 (新鲜度 SLA)")
    return issues


if __name__ == "__main__":
    import sys
    import yaml
    ok = 0
    for p in sys.argv[1:]:
        with open(p, "r", encoding="utf-8") as f:
            cop = yaml.safe_load(f)
        try:
            check_cop(cop, strict=True)
            print("[PASS] %s" % p)
            ok += 1
        except StanceViolation as e:
            print("[VIOLATION] %s :: %s" % (p, e))
    sys.exit(0 if ok == len(sys.argv) - 1 else 1)
