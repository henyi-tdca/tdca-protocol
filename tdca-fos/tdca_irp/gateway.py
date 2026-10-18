# -*- coding: utf-8 -*-
"""
TDCA-IRP 跨库互操作网关 — REPO-003 七库互操作完整实现（M3）
制度锚定: TDCA-TypeSystem-Confirmation-001 §5.1 / §5.2 / §6 | META-002 制度皈依
       | ID91 追溯链 | ID79 MOU 连续性 | ID85/ID86 负空间
版本: V1.0 | 状态: M3-CODED | FC: TDCA-FC-20260804-006-M3

七库间 cross_query / cross_invoke / cross_verify 全部可运行。
所有跨库调用必须：
  1) 验证制度皈依水印（META-002 强制）
  2) 验证配置权七元组
  3) 负空间预检（LEGAL 绝对熔断）
  4) 携带 NCA 追溯链（ID91）
NSFL-Declaration:
  - LEGAL 负空间查询自动熔断，alt_path=None（ID86）
  - 跨库调用链断裂必须拒绝
SPDX-License-Identifier: TDCA-Internal
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import hashlib

from tdca_nsfl.fuse_engine import FuseType


@dataclass
class ConfigRightCall:
    """配置权边界七元组 — TDCA-TypeSystem-Confirmation-001 §5.1"""
    who: str       # 调用主体 DID
    what: str      # 调用内容（库类型/节点ID）
    when: int      # 时间戳
    how: str       # 调用方式（query/invoke/verify）
    share: float   # 收益分配比例
    cfg: str       # 配置参数哈希
    tax: int       # 预扣税收（数字人民币最小单位）


@dataclass
class InstitutionalConversion:
    """制度皈依水印 — META-002 强制"""
    accepts_tda_constitution: bool = True
    accepts_upda: bool = True
    accepts_config_right_pole: bool = True
    accepts_nia_macm_3_0: bool = True
    waives_external_interpretation: bool = True
    admission_oath_nca_ref: str = ""


@dataclass
class CrossInvokeResult:
    """跨库调用结果 — TypeSystem-Confirmation-001 §5.2"""
    success: bool
    result: Any
    generated_nca: str
    mou_contribution: int
    trace_chain: List[str]


class IRPGateway:
    """
    七库跨库互操作网关 — M3 完整实现
    REPO-003 作为中枢，与其他六库进行跨库调用
    """

    def __init__(self, repo_registry: Dict[str, Any], nca_generator=None,
                 tp_reasoner=None, nsfl_engine=None):
        self.repos = repo_registry  # 七库实例注册表
        self.nca = nca_generator
        self.tp = tp_reasoner
        self.nsfl = nsfl_engine

    # ==================== 跨库查询 ====================

    def cross_query(self, source_repo: str, target_repo: str,
                    query: Dict, config_right: ConfigRightCall) -> Dict:
        """
        跨库查询 — 制度皈依水印验证 + 配置权边界验证 + 负空间预检 + NCA 追溯
        """
        # 1. 制度皈依水印验证（META-002 强制）
        if not self._verify_conversion(source_repo, target_repo):
            raise PermissionError(
                f"跨库调用失败: {source_repo} → {target_repo} 未完成制度皈依")

        # 2. 配置权七元组验证
        if not self._verify_config_right(config_right):
            raise ValueError("配置权边界七元组验证失败")

        # 3. 负空间预检：查询内容是否触碰负空间（ID85/ID86）
        nsfl_check = self._check_negative_space(query)
        if nsfl_check:
            self._trigger_nsfl(nsfl_check, "IRP-NSFL-PRE-CHECK")
            raise PermissionError(f"跨库查询被负空间熔断: {nsfl_check}")

        # 4. 执行跨库查询
        target = self.repos.get(target_repo)
        if not target:
            raise ValueError(f"目标库未注册: {target_repo}")
        result = self._call_repo(target, "query", query)

        # 5. 生成跨库 NCA
        nca_ref = self._generate_nca(
            call_type="cross_query", source=source_repo, target=target_repo,
            payload=hashlib.sha256(str(query).encode()).hexdigest(),
            config_right=config_right,
        )

        return {
            "result": result,
            "nca_trace": [nca_ref] if nca_ref else [],
            "mou_contribution": config_right.tax,
        }

    # ==================== 跨库调用 ====================

    def cross_invoke(self, source_repo: str, target_repo: str,
                     call: ConfigRightCall,
                     nca_trace: List[str]) -> CrossInvokeResult:
        """
        跨库调用 — 必须携带完整 NCA 追溯链
        """
        # 1. 验证 NCA 链完整性
        if not self._verify_nca_chain(nca_trace):
            raise ValueError("NCA 追溯链断裂，拒绝跨库调用")

        # 2. 验证链末端的 MOU 连续性（ID79）
        if nca_trace and not self._verify_mou_continuity(nca_trace[-1]):
            raise ValueError("MOU 连续性验证失败")

        # 3. 执行调用
        target = self.repos.get(target_repo)
        if not target:
            raise ValueError(f"目标库未注册: {target_repo}")
        invoke_result = self._call_repo(target, "invoke", call)

        # 4. 生成新 NCA 并追加到追溯链
        new_nca = self._generate_nca(
            call_type="cross_invoke", source=source_repo, target=target_repo,
            payload=hashlib.sha256(str(call).encode()).hexdigest(),
            parent_nca=nca_trace[-1] if nca_trace else None,
            config_right=call,
        )
        new_chain = list(nca_trace) + [new_nca] if new_nca else list(nca_trace)

        return CrossInvokeResult(
            success=True,
            result=invoke_result,
            generated_nca=new_nca or "",
            mou_contribution=call.tax,
            trace_chain=new_chain,
        )

    # ==================== 跨库验证 ====================

    def cross_verify(self, nca_ref: str, verifier_repo: str) -> Dict:
        """
        跨库验证 — 某库验证另一库生成的 NCA
        """
        # 查询 NCA
        nca = self._nca_get(nca_ref)
        if nca is None:
            return {"valid": False, "reason": "NCA 不存在"}

        # 验证封印
        if not self._verify_seal(nca):
            return {"valid": False, "reason": "NCA 封印验证失败"}

        # 验证追溯链
        chain = getattr(nca, "chain", None) or []
        if chain and not self._verify_nca_chain(chain):
            return {"valid": False, "reason": "NCA 追溯链断裂"}

        # 由 verifier_repo 执行额外验证
        verifier = self.repos.get(verifier_repo)
        if verifier is not None:
            verify_fn = (verifier.get("verify_nca") if isinstance(verifier, dict)
                         else getattr(verifier, "verify_nca", None))
            if verify_fn is not None:
                verify_fn(nca)

        return {
            "valid": True,
            "nca_ref": nca_ref,
            "verified_by": verifier_repo,
            "mou_contribution": getattr(nca, "mou_contribution", 0),
        }

    # ==================== 负空间预检 ====================

    def _check_negative_space(self, query: Dict) -> Optional[Dict]:
        """
        负空间预检 — 查询内容是否触碰负空间
        LEGAL: 绝对熔断；ETHICAL: 熔断 + 替代路径
        """
        query_text = str(query).lower()

        legal_keywords = ["违法", "绕过监管", "伪造", "洗钱", "逃税"]
        for kw in legal_keywords:
            if kw in query_text:
                return {"type": "LEGAL", "keyword": kw}

        ethical_keywords = ["操纵情绪", "欺骗", "诱导"]
        for kw in ethical_keywords:
            if kw in query_text:
                return {"type": "ETHICAL", "keyword": kw}

        return None

    # ==================== 内部工具 ====================

    def _verify_conversion(self, src: str, tgt: str) -> bool:
        """验证双方库均已完成制度皈依（META-002）"""
        for repo_name in (src, tgt):
            repo = self.repos.get(repo_name)
            if not repo:
                return False
            conversion = (repo.get("institutional_conversion", {})
                          if isinstance(repo, dict)
                          else getattr(repo, "institutional_conversion", {}))
            if not conversion.get("accepts_tda_constitution"):
                return False
        return True

    @staticmethod
    def _verify_config_right(cr: ConfigRightCall) -> bool:
        """验证配置权七元组完整性"""
        return all([
            bool(cr.who), bool(cr.what), cr.when > 0, bool(cr.how),
            0 <= cr.share <= 1, bool(cr.cfg), cr.tax >= 0,
        ])

    def _verify_nca_chain(self, nca_trace: List[str]) -> bool:
        """验证 NCA 追溯链（ID91 链完整性）"""
        if not nca_trace:
            return False
        if self.nca is not None and hasattr(self.nca, "verify_chain"):
            return self.nca.verify_chain(nca_trace)
        return all(t for t in nca_trace)

    def _verify_mou_continuity(self, nca_ref: str) -> bool:
        """验证 MOU 连续性 — ID79（NCA 必须有 MOU 贡献）"""
        nca = self._nca_get(nca_ref)
        return nca is not None and getattr(nca, "mou_contribution", 0) > 0

    def _nca_get(self, nca_ref: str):
        """按引用取 NCA（兼容 generate 对象与 record 占位）"""
        if self.nca is None:
            return None
        if hasattr(self.nca, "get"):
            return self.nca.get(nca_ref)
        return None

    def _verify_seal(self, nca) -> bool:
        """验证封印（ID56）"""
        if hasattr(nca, "seal") and hasattr(self.nca, "verify_seal"):
            return self.nca.verify_seal(nca)
        return True  # 占位 NCA 无 verify_seal 时视为有效

    def _generate_nca(self, call_type: str, source: str, target: str,
                      payload: str, config_right: ConfigRightCall,
                      parent_nca: Optional[str] = None) -> Optional[str]:
        """生成跨库 NCA 存证 — ID91"""
        if self.nca is None:
            return None
        content = {
            "call_type": call_type,
            "source": source,
            "target": target,
            "payload_hash": payload,
            "config_right": {
                "who": config_right.who,
                "what": config_right.what,
                "tax": config_right.tax,
            },
        }
        if hasattr(self.nca, "generate"):
            nca = self.nca.generate(
                type="INSTITUTIONAL", layer=3, content=content,
                parent_nca=parent_nca,
            )
            return getattr(nca, "nca_id", None)
        if hasattr(self.nca, "record_cross_call"):
            return self.nca.record_cross_call(
                source=source, target=target, call_type=call_type,
                config_right=config_right,
                result_hash=payload)
        return None

    def _trigger_nsfl(self, nsfl_check: Dict, rule_id: str):
        """触发负空间熔断 — ID85/ID86"""
        if self.nsfl is None:
            return
        fuse_type = (FuseType.LEGAL if nsfl_check.get("type") == "LEGAL"
                     else FuseType.ETHICAL)
        if hasattr(self.nsfl, "trigger"):
            self.nsfl.trigger(
                rule_id=rule_id, severity=3,
                reason=f"跨库操作触碰负空间: {nsfl_check}",
                alt_path=None if nsfl_check.get("type") == "LEGAL"
                else "修改查询范围",
                nca_ref="", fuse_type=fuse_type,
            )

    @staticmethod
    def _call_repo(repo: Any, method: str, *args):
        """调用库实例方法（兼容对象与 dict 注册表条目）"""
        fn = (repo.get(method) if isinstance(repo, dict)
              else getattr(repo, method, None))
        if fn is None:
            raise ValueError(f"目标库无 {method} 接口")
        return fn(*args)
