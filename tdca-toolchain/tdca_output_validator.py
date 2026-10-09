"""
TDCA-FC-20260802-004 修正声明:
  - R1-P1: Max-Retry 语义层级区分
    (制度层 Max-Retry=0: 配置权调用失败不重试
     技术层内部重试 ≤3次: 输出校验快系统内部优化, 不触及配置权边界, 不生成新NCA)
  - R1-P1: embedding 三级降级策略
    (主路径: embedding API → 降级1: 本地sentence-transformers → 降级2: Jaccard → 降级3: HUMAN_REQUIRED)
  - R1-P2: 执行顺序并行化

制度锚定: TDCA-PRINCIPLE-FC-NCA-COH-002(三阶验证: 输出校验)
Granted-By: TDCA-PRINCIPLE-FC-NCA-COH-002

NSFL-Declaration:
  - 触碰 ⊗ 禁止集合立即 DENIED
  - 任何降级路径必须生成 Audit-Trail 记录
  - 内部重试不生成新的配置权调用记录
SPDX-License-Identifier: TDCA-Internal
"""

import enum
import json
from dataclasses import dataclass, field, asdict
from typing import Optional


class ValidationStatus(enum.Enum):
    """输出校验状态"""
    PASS = "PASS"
    FAIL = "FAIL"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"   # 降级3: 交由人类裁决


class EmbeddingLevel(enum.Enum):
    """embedding 降级级别"""
    API = "API"                          # 主路径: embedding API 语义余弦距离
    LOCAL = "LOCAL"                      # 降级1: 本地 sentence-transformers
    JACCARD = "JACCARD"                  # 降级2: 字符级 Jaccard 相似度
    HUMAN = "HUMAN"                      # 降级3: 返回 HUMAN_REQUIRED


@dataclass
class ValidationResult:
    """输出校验结果"""
    status: ValidationStatus
    similarity: float
    embedding_level: EmbeddingLevel
    audit_trail: list = field(default_factory=list)
    retry_count: int = 0
    reason: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d['status'] = self.status.value
        d['embedding_level'] = self.embedding_level.value
        return d


class TDCAOutputValidator:
    """
    模型输出后的自动校验层（快系统）

    核心约束:
      - 毫秒级响应（快系统）
      - 计算输出与目标函数的语义距离
      - 距离超出阈值 → 自动拒绝 → 触发重试（≤3次）→ 仍失败则上报人类
      - 内部重试不生成新的配置权调用记录
      - 触碰 ⊗ 禁止集合立即 DENIED
    """

    MAX_RETRY = 3  # 技术层内部重试上限（不触及配置权边界）

    def __init__(self, embedding_func: Optional[callable] = None):
        """
        参数:
          embedding_func: 语义相似度计算函数 (a, b) -> float [0,1]
                          未提供时使用降级策略
        """
        self._embedding_func = embedding_func
        self._audit_log = []

    def validate(
        self,
        output: str,
        target_function: callable,
        constraint_matrix: dict,
        tolerance: float = 0.05
    ) -> ValidationResult:
        """
        校验流程:
          1. 语义距离计算：||输出 - 目标函数||（嵌入空间余弦距离或逻辑满足度）
          2. 约束矩阵检查：输出是否触碰 ⊗ 禁止集合
          3. 逼近度判定：δ < Δ_max ? PASS : FAIL
          4. 失败处理：触发重试（≤3次）→ 仍失败则上报人类（慢系统）
        """
        audit = []

        # 步骤2（先检查约束）：输出触碰 ⊗ 禁止集合 → 立即 DENIED
        nsfl_check = self._check_nsfl(output, constraint_matrix)
        audit.append({'step': 'nsfl_check', 'result': nsfl_check})
        if nsfl_check == 'DENIED':
            return ValidationResult(
                status=ValidationStatus.FAIL,
                similarity=0.0,
                embedding_level=EmbeddingLevel.JACCARD,
                audit_trail=audit,
                retry_count=0,
                reason="输出触碰 ⊗ 禁止集合",
            )

        # 步骤1 + 3：语义距离计算与逼近度判定（含内部重试）
        retries = 0
        while retries <= self.MAX_RETRY:
            similarity, level = self._compute_similarity(output, target_function)
            audit.append({
                'step': f'similarity_attempt_{retries + 1}',
                'similarity': similarity,
                'level': level.value,
                'retry': retries,
            })

            # 降级3: 无法计算 → HUMAN_REQUIRED
            if level == EmbeddingLevel.HUMAN:
                return ValidationResult(
                    status=ValidationStatus.HUMAN_REQUIRED,
                    similarity=0.0,
                    embedding_level=level,
                    audit_trail=audit,
                    retry_count=retries,
                    reason="embedding 计算失败，交由人类裁决",
                )

            if similarity >= (1.0 - tolerance):
                return ValidationResult(
                    status=ValidationStatus.PASS,
                    similarity=similarity,
                    embedding_level=level,
                    audit_trail=audit,
                    retry_count=retries,
                    reason=f"输出逼近目标函数 (相似度 {similarity:.4f})",
                )

            retries += 1

        # 重试耗尽 → 上报人类（慢系统）
        return ValidationResult(
            status=ValidationStatus.HUMAN_REQUIRED,
            similarity=similarity,
            embedding_level=level,
            audit_trail=audit,
            retry_count=self.MAX_RETRY,
            reason=f"重试 {self.MAX_RETRY} 次仍无法通过校验，上报人类",
        )

    # ---- 相似度计算（三级降级）----

    def _compute_similarity(self, output: str, target_function: callable) -> tuple:
        """
        三级降级策略:
          主路径: embedding_func 提供 → 余弦距离
          降级1: 本地 sentence-transformers（若可用）
          降级2: 字符级 Jaccard 相似度
          降级3: 返回 HUMAN_REQUIRED
        任何降级路径都生成 Audit-Trail（由调用方记录）。
        """
        # 主路径: 用户提供的 embedding 函数
        if self._embedding_func is not None:
            try:
                sim = self._embedding_func(output, target_function)
                return float(max(0.0, min(1.0, sim))), EmbeddingLevel.API
            except Exception:
                pass

        # 降级1: 本地 sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer, util
            if not hasattr(self, '_local_model'):
                self._local_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            emb1 = self._local_model.encode(output)
            emb2 = self._local_model.encode(self._target_text(target_function))
            sim = util.cos_sim(emb1, emb2).item()
            return float(max(0.0, min(1.0, sim))), EmbeddingLevel.LOCAL
        except ImportError:
            pass
        except Exception:
            pass

        # 降级2: 字符级 Jaccard 相似度
        try:
            sim = self._jaccard(output, self._target_text(target_function))
            return float(sim), EmbeddingLevel.JACCARD
        except Exception:
            pass

        # 降级3: 无法计算 → HUMAN_REQUIRED
        return 0.0, EmbeddingLevel.HUMAN

    @staticmethod
    def _target_text(target_function) -> str:
        """
        将目标函数转换为可比对的文本，兼容三种输入类型:
          - dict (IR): 提取 target_function_formalized.expression
          - str: 直接使用
          - callable: 安全调用探测（失败退回 repr）

        NSFL: 任何类型处理失败都不得静默返回空字符串
        """
        # 类型1: dict（IR 对象）
        if isinstance(target_function, dict):
            formalized = target_function.get('target_function_formalized', {})
            expr = formalized.get('expression') if isinstance(formalized, dict) else None
            if expr:
                return str(expr)
            return str(target_function)

        # 类型2: str
        if isinstance(target_function, str):
            return target_function

        # 类型3: callable（安全调用探测）
        if callable(target_function):
            try:
                result = target_function("__TDCA_TARGET_PROBE__")
                if isinstance(result, str):
                    return result
            except Exception:
                pass

        # 兜底: 字符串化（repr）
        return str(target_function)

    @staticmethod
    def _jaccard(a: str, b: str) -> float:
        """字符级 Jaccard 相似度"""
        set_a = set(a)
        set_b = set(b)
        if not set_a and not set_b:
            return 1.0
        inter = len(set_a & set_b)
        union = len(set_a | set_b)
        return inter / union if union > 0 else 0.0

    # ---- NSFL 检查 ----

    def _check_nsfl(self, output: str, constraint_matrix: dict) -> str:
        """检查输出是否触碰禁止集合"""
        forbidden = constraint_matrix.get('forbidden', [])
        for item in forbidden:
            if isinstance(item, str) and item in output:
                return 'DENIED'
        return 'PASS'


# ---- CLI ----
if __name__ == '__main__':
    import sys

    def identity_func(x):
        return x

    validator = TDCAOutputValidator()
    test_output = sys.argv[1] if len(sys.argv) > 1 else "test"
    result = validator.validate(
        output=test_output,
        target_function=identity_func,
        constraint_matrix={'forbidden': ['__FORBIDDEN__']},
        tolerance=0.5
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
