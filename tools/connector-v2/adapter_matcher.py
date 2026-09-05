# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
"""TDCA 适配器 L4 自动化：标准条款 → 原理 ID 匹配辅助工具

输入：合规标准条款（如「最小权限」「人工确认」「熔断」）
输出：Top-K 匹配的 TDCA 原理 ID + 说明（辅助适配器实例的映射详表填写）
"""
import sys
import re
import math
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

# TDCA 原理 ID 索引（ID29~ID93 精选，名称 + 核心关键词）
PRINCIPLES = {
    'ID29': ('制度基座第一性', '制度基座 不可还原 技术基座 配置对象 基座 第一性'),
    'ID31': ('最简机制设计', '最少规则 最大秩序 最简机制 机制设计'),
    'ID32': ('制度红利大于技术红利', '制度红利 技术红利 秩序 累积性 网络锁定 不可复制'),
    'ID33': ('制度辩证论/活宪法', '活宪法 OTA 升级 制度辩证 修订 改进 更新'),
    'ID35': ('制度-技术同构', '制度 技术 同构 映射 对齐'),
    'ID36': ('制度-技术动态均衡', '动态均衡 双向校准 均衡 改进 校准'),
    'ID38': ('破例识别原理', '破例 伪创新 例外 绕过'),
    'ID42': ('效用触发确权', '效用触发 确权 单一场景效用函数 触发'),
    'ID60': ('不对称对齐', '不对称对齐 认知不对称 异构性'),
    'ID65': ('实践本体论', '实践 本体论 制度事实 真理'),
    'ID68': ('Protocolizer 六要素', '六要素 目标函数 约束矩阵 先验分布 配置权边界 预期分配 审计轨迹'),
    'ID71': ('快与慢战略', '快系统 慢系统 快慢 分工 人类签名 最终签名权'),
    'ID76': ('配置权第三极', '配置权 第三极 协作调度权 调度 权限 分级 授权'),
    'ID77': ('新经济法则', '被调用 知识 价值 协议层免费 资产专用税 调用'),
    'ID78': ('黑箱反馈闭环', '黑箱 反馈闭环 过程不可知 闭环'),
    'ID79': ('MOU 原理', 'MOU 税收锚定 最低可见效用 硬下限 锚定 税收'),
    'ID80': ('CBDC 唯一性', '数字人民币 智能合约 CBDC 央行 货币'),
    'ID81': ('五元拓扑空间', '五元拓扑 拓扑空间 坐标卡 局部坐标 拓扑'),
    'ID82': ('制度同构跃进', '制度同构 跃进 编译 非蒸馏 同构'),
    'ID84': ('协作停机定理', '停机 终止条件 满意解 充分解 资源耗尽'),
    'ID85': ('负空间函数语言', '负空间 熔断 禁止 限制 观察 函数语言'),
    'ID86': ('法律负空间第二边界', '法律 负空间 第二边界 立法 司法'),
    'ID89': ('化学热力学原理簇', '化合 化学热力学 活化能 化合物 析构'),
    'ID90': ('最小化合原则', '最小化合 物理叠加 化学反应 不可拆分 最小'),
    'ID91': ('自反化合原理', '自反 化合 自指 递归'),
    'ID93': ('术语合规协议', '术语 合规 名词 协议 口径'),
}

PUNCT = re.compile(r'[，。、；：？！“”‘’（）【】《》\s·—…/\\|\[\](){}<>]+')


def tokenize(text):
    text = PUNCT.sub(' ', text or '')
    try:
        import jieba
        words = [w.strip() for w in jieba.cut(text) if w.strip()]
    except ImportError:
        clean = re.sub(r'\s+', '', text)
        words = [clean[i:i+n] for n in (2, 3) for i in range(len(clean)-n+1)]
    return [w for w in words if len(w) >= 2 and not re.fullmatch(r'[\d\.\%\:：\-]+', w)]


def match_clause(clause, top_k=5):
    """标准条款 → Top-K 原理 ID 匹配（关键词余弦 + 原理关键词子串命中加权）"""
    clause_tokens = tokenize(clause)
    clause_vec = Counter(clause_tokens)
    results = []
    for pid, (name, kw_text) in PRINCIPLES.items():
        kw_tokens = tokenize(kw_text)
        # 命中数 + 余弦
        hit = set(clause_tokens) & set(kw_tokens)
        hit_score = len(hit) / max(1, len(clause_tokens))
        # 余弦相似度
        kw_vec = Counter(kw_tokens)
        common = set(clause_vec) & set(kw_vec)
        dot = sum(clause_vec[k] * kw_vec[k] for k in common)
        na = math.sqrt(sum(v*v for v in clause_vec.values()))
        nb = math.sqrt(sum(v*v for v in kw_vec.values()))
        cos = dot / (na * nb) if na and nb else 0.0
        score = 0.6 * hit_score + 0.4 * cos
        if hit or cos > 0:
            results.append({'id': pid, 'name': name, 'score': round(score, 3),
                            'hit': sorted(hit)})
    results.sort(key=lambda r: -r['score'])
    return results[:top_k]


if __name__ == '__main__':
    clauses = [
        "最小权限原则：智能体仅授予完成任务所需的最低权限",
        "人工确认：高风险操作需人类审批后才可执行",
        "熔断机制：检测到异常行为时自动暂停智能体运行",
        "全链路日志：记录智能体每步推理与工具调用，支持审计溯源",
        "数据最小化：仅提供任务必需数据，多租户记忆隔离",
        "持续改进：定期复盘风险事件并更新控制措施",
    ]
    print("=" * 72)
    print("TDCA 适配器 L4 自动化：标准条款 → 原理 ID 匹配")
    print("=" * 72)
    for clause in clauses:
        print(f"\n【条款】{clause}")
        print("-" * 72)
        for r in match_clause(clause, top_k=3):
            print(f"  {r['id']}  {r['name']:　<16} 得分={r['score']:.3f}  命中={r['hit']}")
