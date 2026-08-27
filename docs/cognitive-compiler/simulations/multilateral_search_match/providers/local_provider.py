# -*- coding: utf-8 -*-
"""本地候选源 —— 内置 8 范式主体 + 可合成"海量"以压测算力层
=========================================================
原型阶段"真实全网"以本地库演示算法; 用 --scale N 可合成 N 个
候选主体, 证明并行遍历 / 剪枝 / 蒙特卡洛夏普利在海量规模仍可控。
"""
import os
import random
import yaml
from .base import Candidate, CandidateProvider

# 内置 8 个真实范式主体 (与 v1 引擎一致, 保证可复现对照)
_BUILTIN = [
    {"id": "A", "name": "盛元智造", "cop": "围魏救赵",
     "res": {"制造": 0.95, "渠道": 0.20, "算力": 0.15, "数据": 0.20, "模型": 0.10, "资本": 0.50, "合规": 0.55, "IP": 0.35}, "batna": 18},
    {"id": "B", "name": "云渠通联", "cop": "走为上",
     "res": {"制造": 0.10, "渠道": 0.95, "算力": 0.20, "数据": 0.25, "模型": 0.15, "资本": 0.30, "合规": 0.55, "IP": 0.20}, "batna": 20},
    {"id": "C", "name": "数擎云", "cop": "博弈论·机制设计",
     "res": {"制造": 0.15, "渠道": 0.30, "算力": 0.95, "数据": 0.90, "模型": 0.85, "资本": 0.45, "合规": 0.50, "IP": 0.40}, "batna": 22},
    {"id": "D", "name": "链安合规", "cop": "制度合规",
     "res": {"制造": 0.20, "渠道": 0.25, "算力": 0.30, "数据": 0.30, "模型": 0.25, "资本": 0.30, "合规": 0.95, "IP": 0.30}, "batna": 15},
    {"id": "E", "name": "资桥资本", "cop": "金融·资本调度",
     "res": {"制造": 0.20, "渠道": 0.30, "算力": 0.25, "数据": 0.20, "模型": 0.20, "资本": 0.95, "合规": 0.45, "IP": 0.25}, "batna": 24},
    {"id": "F", "name": "知产所", "cop": "知识产权",
     "res": {"制造": 0.20, "渠道": 0.25, "算力": 0.30, "数据": 0.35, "模型": 0.45, "资本": 0.30, "合规": 0.60, "IP": 0.95}, "batna": 16},
    {"id": "G", "name": "智研院", "cop": "学术·系统思考",
     "res": {"制造": 0.30, "渠道": 0.25, "算力": 0.55, "数据": 0.55, "模型": 0.90, "资本": 0.30, "合规": 0.45, "IP": 0.55}, "batna": 19},
    {"id": "H", "name": "边算科技", "cop": "边缘计算",
     "res": {"制造": 0.25, "渠道": 0.35, "算力": 0.70, "数据": 0.50, "模型": 0.55, "资本": 0.35, "合规": 0.50, "IP": 0.30}, "batna": 17},
]

# 合成主体命名池 (让海量候选有可读标签)
_SYN_NAMES = ["翼算", "恒通", "云栖", "链信", "智擎", "数澜", "盈科", "寰宇",
              "锐合", "元启", "汇融", "泰联", "星枢", "砺石", "澄源", "序轮"]


def _builtin_eight(dims):
    return [Candidate(id=c["id"], name=c["name"], cop=c["cop"],
                      res={d: float(c["res"].get(d, 0.0)) for d in dims},
                      batna=float(c["batna"]), source="local-builtin") for c in _BUILTIN]


def _synthesize(n, dims, seed, exclude):
    """合成 n 个候选主体 (确定性随机, 模拟"海量"主体库)。
    关键: 让主体**专业化**——基础值低, 仅 1~3 个维度高强度。
    这制造真实的互补结构 (每个主体只擅长少数维度), 才需要"比配"撮合,
    而非单个全能体直接全覆盖。"""
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        cid = "S%03d" % (i + 1)
        if cid in exclude:
            continue
        res = {d: round(rnd.uniform(0.02, 0.22), 2) for d in dims}  # 基础值低
        hot_n = rnd.randint(1, 3)                                   # 1~3 个专精维度
        for hot in rnd.sample(dims, hot_n):
            res[hot] = round(min(1.0, rnd.uniform(0.6, 0.98)), 2)
        nm = _SYN_NAMES[i % len(_SYN_NAMES)] + ("·%d" % (i // len(_SYN_NAMES) + 1))
        out.append(Candidate(id=cid, name=nm, cop="合成·%s域" % rnd.choice(dims),
                             res=res, batna=round(rnd.uniform(10, 26), 1),
                             source="local-synthetic"))
    return out


class LocalProvider(CandidateProvider):
    def __init__(self, path=None, scale=0, seed=42):
        self.path = path
        self.scale = scale          # 在真实 8 主体之外合成多少候选以模拟"海量"
        self.seed = seed

    @property
    def source_name(self):
        return "local" + (f"+synthetic({self.scale})" if self.scale else "")

    def load(self, dims, task_id=""):
        cands = []
        if self.path and os.path.isfile(self.path):
            with open(self.path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            for c in data.get("candidates", []):
                cands.append(Candidate(
                    id=str(c["id"]), name=str(c.get("name", "")), cop=str(c.get("cop", "")),
                    res={d: float(c.get("res", {}).get(d, 0.0)) for d in dims},
                    batna=float(c.get("batna", 0)), source="local-file"))
        else:
            cands = _builtin_eight(dims)
        if self.scale and self.scale > 0:
            cands += _synthesize(self.scale, dims, self.seed, {c.id for c in cands})
        return cands
