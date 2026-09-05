# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
"""TDCA 连接器 v2（语义向量升级）：TF-IDF 加权 + 多维语义匹配 + 负空间反向信号

升级点（对比 v1 词袋）：
  1. 多维特征分离：soul / primitives / decision / negative_space 四维
  2. TF-IDF 加权：降低「协作/调度/管理」等通用词权重，提升「正和/涌现/熔断」等特征词权重
  3. 多维加权余弦：A = 0.5·cos(soul) + 0.3·cos(prim) + 0.2·cos(decision)
  4. 负空间反向：场景需求命中 COP negative_space → A 下调（禁忌匹配）

核心算法仍锚定 S1：U(c|s) = U₀(c) · SC(s) · A(c,s)
"""
import os
import re
import sys
import math
import yaml
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

WS = r"C:\Users\22850\AppData\Roaming\reasonix\global-workspace"
COP_DIR = os.path.join(WS, r"tdca-thinktank\research\topics\thinking-protocol\cop-library")

STOPWORDS = set("""的 了 与 和 及 或 在 是 为 于 之 其 中 被 把 让 使 用 对 向 从 到 自 而 且 但 却 则 已 将 会 能 可 应 需 有 无 不 非 是 否 一个 一种 这个 那个 这些 那些 我们 你们 他们 通过 进行 实现 产生 形成 需要 可以 应当 必须 用于 作为 以及 或者 并且 因为 所以 如果 那么 从而 因此 相关 问题 情况 方式 方法 过程 结果 目标 主体 对象 内容 范围 边界 约束 条件 前提 后件 步骤 流程 机制 规则 体系 结构 功能 作用 意义 价值 效用 场景 协作 调用 配置 分配 收益 风险 安全 合规 审计 存证 治理 制度 协议 思维 认知 决策 执行 验证 评估 检测 监测 管理 控制 调度 编排 组合 化合 分解 抽象 具体 整体 局部 全局 动态 静态 线性 非线性 对称 不对称 同构 异构""".split())

PUNCT = re.compile(r'[，。、；：？！“”‘’（）【】《》\s·—…/\\|\[\](){}<>]+')


def tokenize(text: str):
    text = PUNCT.sub(' ', text or '')
    try:
        import jieba
        words = [w.strip() for w in jieba.cut(text) if w.strip()]
    except ImportError:
        clean = re.sub(r'\s+', '', text)
        words = []
        for n in (2, 3, 4):
            for i in range(len(clean) - n + 1):
                words.append(clean[i:i + n])
    out = []
    for w in words:
        if w in STOPWORDS or len(w) < 2:
            continue
        if re.fullmatch(r'[\d\.\%\:：\-]+', w):
            continue
        out.append(w)
    return out


def load_cops(cop_dir: str):
    """扫描 cop-library，提取多维特征（soul/prim/decision/negative）"""
    cops = []
    for root, _, files in os.walk(cop_dir):
        for fn in files:
            if not fn.endswith('.yaml'):
                continue
            p = os.path.join(root, fn)
            try:
                d = yaml.safe_load(open(p, encoding='utf-8'))
            except Exception:
                continue
            if not isinstance(d, dict) or 'soul' not in d:
                continue
            soul = d.get('soul', {})
            prims = d.get('primitives', []) or []
            dec = d.get('decision', []) or []
            neg = d.get('negative_space', []) or []
            soul_text = ' '.join([str(soul.get('identity', '')), str(soul.get('core', '')),
                                  str(soul.get('role', '')), str(soul.get('category', ''))])
            prim_text = ' '.join([str(x.get('method', '')) + ' ' + str(x.get('precond', ''))
                                  + ' ' + str(x.get('postcond', '')) for x in prims])
            decision_text = ' '.join([str(x.get('if', '')) + ' ' + str(x.get('call', '')) for x in dec])
            negative_text = ' '.join(str(x) for x in neg)
            cops.append({
                'cop_id': d.get('COP-ID', fn.replace('.yaml', '')),
                'identity': soul.get('identity', ''),
                'category': soul.get('category', ''),
                'core': soul.get('core', ''),
                'soul_vec': Counter(tokenize(soul_text)),
                'prim_vec': Counter(tokenize(prim_text)),
                'decision_vec': Counter(tokenize(decision_text)),
                'negative_terms': set(tokenize(negative_text)),
                'validated': bool(d.get('validation', {}).get('passed')),
                'n_prims': len(prims),
                'n_dec': len(dec),
                'nca_emit': bool(prims and prims[0].get('nca_emit')),
            })
    return cops


def compute_idf(cops, field):
    """IDF = log(N / (1 + df))，降低高频通用词权重"""
    N = len(cops)
    df = Counter()
    for cop in cops:
        for w in set(cop[field]):
            df[w] += 1
    return {w: math.log((N + 1) / (1 + df[w])) + 1.0 for w in df}


def weighted_cosine(vec_a: Counter, vec_b: Counter, idf: dict) -> float:
    """带 IDF 加权的余弦相似度"""
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] * (idf.get(k, 1.0) ** 2) for k in common)
    na = math.sqrt(sum((v * idf.get(k, 1.0)) ** 2 for k, v in vec_a.items()))
    nb = math.sqrt(sum((v * idf.get(k, 1.0)) ** 2 for k, v in vec_b.items()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def compute_u0(cop):
    """U₀(c)：COP 基准效用（编译期定值）

    S1：U₀(c) = 函数语料六要素中 objective 的归一化评分（非内禀价值，是「潜力基量」）。
    工程化代理：validation.passed 是硬门槛（未通过=0），编译质量 = 原语丰富度 + 决策复杂度 + NCA 发射。
    """
    if not cop.get('validated'):
        return 0.0  # 未通过验证的 COP 硬排除
    n_prims = cop.get('n_prims', 0)
    n_dec = cop.get('n_dec', 0)
    nca = 1.0 if cop.get('nca_emit') else 0.5
    # 归一化编译质量（0~1）
    quality = min(1.0, 0.5 + 0.15 * min(n_prims, 4) + 0.1 * min(n_dec, 4) + 0.2 * nca)
    return round(quality, 4)


def match(scene_desc: str, cops, top_k: int = 5, scene_weight: float = 1.0, base_utility: float = None,
          verbose: bool = False):
    """多维语义匹配：A = 0.5·cos(soul) + 0.3·cos(prim) + 0.2·cos(decision)，负空间反向下调"""
    scene_vec = Counter(tokenize(scene_desc))
    idf_soul = compute_idf(cops, 'soul_vec')
    idf_prim = compute_idf(cops, 'prim_vec')
    idf_dec = compute_idf(cops, 'decision_vec')

    results = []
    for cop in cops:
        a_soul = weighted_cosine(cop['soul_vec'], scene_vec, idf_soul)
        a_prim = weighted_cosine(cop['prim_vec'], scene_vec, idf_prim)
        a_dec = weighted_cosine(cop['decision_vec'], scene_vec, idf_dec)
        A = 0.5 * a_soul + 0.3 * a_prim + 0.2 * a_dec
        # 负空间反向：只对 ≥3 字的禁忌短语生效（避免「数据」「熔断」等 2 字通用词词面巧合误伤）
        neg_hit = {w for w in (set(scene_vec) & cop['negative_terms']) if len(w) >= 3}
        if neg_hit:
            A *= 0.5
        U = (compute_u0(cop) if base_utility is None else base_utility) * scene_weight * A
        results.append({
            'cop_id': cop['cop_id'], 'identity': cop['identity'],
            'category': cop['category'], 'core': cop['core'],
            'A': round(A, 4), 'U': round(U, 4),
            'U0': compute_u0(cop),
            'a_soul': round(a_soul, 3), 'a_prim': round(a_prim, 3), 'a_dec': round(a_dec, 3),
            'neg_hit': list(neg_hit)[:3],
        })
    results.sort(key=lambda r: (-r['U'], -r['A']))
    return results[:top_k]


if __name__ == '__main__':
    cops = load_cops(COP_DIR)
    print(f"COP 索引加载: {len(cops)} 个思维协议（v2 语义向量：TF-IDF + 多维加权 + 负空间反向）")
    print("=" * 74)

    scenes = [
        ("场景1 商业战略转型",
         "企业面临市场萎缩，需要战略转型、隐蔽布局、出其不意抢占新市场，同时规避竞争对手警觉"),
        ("场景2 多主体资源调度",
         "多个智能体协作调度算力与数据资源，需要优先级分配、避免冲突、正和博弈、公平分账"),
        ("场景3 风险合规审查",
         "金融智能体需要审查高风险交易，防范欺诈与洗钱，遵守监管合规，熔断异常行为"),
    ]
    for name, desc in scenes:
        print(f"\n【{name}】 {desc}")
        print("-" * 74)
        top = match(desc, cops, top_k=5)
        for i, r in enumerate(top, 1):
            bar = '█' * int(r['A'] * 30)
            print(f"  {i}. {r['identity']:　<12} U0={r['U0']:.2f} A={r['A']:.3f} U={r['U']:.3f}  {bar}")
            print(f"     [soul={r['a_soul']} prim={r['a_prim']} dec={r['a_dec']}] [{r['category']}] {r['core'][:28]}")
            if r['neg_hit']:
                print(f"     ⚠ 负空间反向命中: {r['neg_hit']}")
