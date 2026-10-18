# -*- coding: utf-8 -*-
"""
TDCA-Graph Query Engine — 五维图查询引擎（TDCA-KG-001 §3.3/§3.4 查询模式）
制度锚定: TDCA-KG-001 §3.3 / §3.4 / §5.3 | ID82 接口熵 | ID91 NCA | ID38
版本: V1.0 | 状态: M1-CODED | FC: TDCA-FC-20260804-006

职责: 实现 TDCA-KG-001 全部核心查询模式，供 DevCluster 查询制度约束。
六要素声明:
  目标函数: 五维图制度约束查询（开发约束/原理/NSFL/函数语料/MRCR/版本差异）
  约束矩阵: ID91 全查询生成 NCA（fail-closed）| ID82 接口熵=0 | ID38 破例识别
  先验分布: TDCA-KG-001 §3.3/§3.4/§5.3 查询模式
  配置权边界: 只读查询，无业务写入（NCA 审计记录除外）
  预期分配: 查询结果 + NCA 引用
  审计轨迹: 每次查询生成 COGNITIVE NCA（AGENT-DEPLOY-001-FOLLOWUP TASK-006 补全）
所有查询必须：
  1) 生成 NCA 审计轨迹（ID91）
  2) 校验接口熵 = 0（ID82）
  3) 支持负空间事件检测（ID85/ID86）
NSFL-Declaration:
  - 查询只读，不写业务数据（NCA 记录除外）
  - 不执行任何 ⊗ 禁止操作符语义
SPDX-License-Identifier: TDCA-Internal
"""

from typing import Dict, List, Any, Optional


class InterfaceEntropyViolation(Exception):
    """接口熵非零违例 — TDCA-PRINCIPLE-INTERFACE-ENTROPY-001 / ID82"""


class NCAGenerationFailure(Exception):
    """NCA 生成失败 — ID91 fail-closed：无 NCA 即拒绝执行（AGENT-DEPLOY-001-FOLLOWUP TASK-006）"""


class TDCAGraphQueryEngine:
    """
    五维图查询引擎
    制度约束：所有查询必须生成 NCA 审计轨迹
    依赖注入：driver 可为真实 neo4j 驱动或内存实现（测试友好）
    """

    def __init__(self, driver, nca_generator=None, current_version: str = "v1.0.0",
                 ota=None):
        """
        :param driver: neo4j GraphDatabase.driver 实例或兼容内存驱动
        :param nca_generator: 可选 NCA 生成器（record_query 接口）
        :param current_version: OTA 版本号
        :param ota: 可选 OTAController 实例（版本差异 API，M4）
        """
        self.driver = driver
        self.nca = nca_generator
        self.current_version = current_version
        self.ota = ota

    # ---- 查询 3.3：开发约束查询 ----

    def get_development_constraints(
        self,
        target_role_id: str,
        target_cluster: str,
        developer_model: str,
        scene_id: str,
    ) -> Dict[str, Any]:
        """
        查询 3.3：代码编写集群开发全周期管理集群所需的全部制度约束
        返回：ConstraintSet（TDCA-KG-001 §3.4）
        """
        query = """
        MATCH path = (dev:AgentRole {cluster: $dev_cluster})-[:COMPILES_TO]->
                     (gov:AgentRole {role_id: $role_id, cluster: $gov_cluster})
        WITH path,
             [p IN nodes(path) WHERE p:Principle | p.id] AS principles,
             [c IN nodes(path) WHERE c:Constitution | c.article] AS articles,
             [n IN nodes(path) WHERE n:NSFLRule | n.id] AS nsfl_rules,
             [f IN nodes(path) WHERE f:FunctionSpec | f] AS function_specs
        RETURN
            gov.role_id AS target_role,
            principles AS required_principles,
            articles AS required_constitutions,
            nsfl_rules AS required_nsfl_rules,
            function_specs AS required_function_specs,
            reduce(entropy = 0, rel IN relationships(path) |
                entropy + CASE WHEN rel.interface_entropy IS NULL THEN 0
                ELSE rel.interface_entropy END
            ) AS total_interface_entropy
        """

        record = self._run_single(query, {
            "dev_cluster": "DEV",
            "role_id": target_role_id,
            "gov_cluster": target_cluster,
        })

        # 接口熵必须为 0（ID82）
        total_entropy = (record or {}).get("total_interface_entropy", 0) or 0
        if total_entropy > 0:
            raise InterfaceEntropyViolation(
                f"接口熵={total_entropy}，违反 TDCA-PRINCIPLE-INTERFACE-ENTROPY-001"
            )

        nca_ref = self._record_nca(
            query_type="GetDevelopmentConstraints",
            parameters={"target_role_id": target_role_id, "scene_id": scene_id},
            result_summary=record or {},
        )

        return {
            "constraint_set": record or {},
            "nca_reference": nca_ref,
            "interface_entropy": 0.0,  # 硬约束
            "version": self.current_version,
        }

    # ---- 查询 1：角色所需制度原理 ----

    def get_required_principles(self, role_id: str) -> List[Dict]:
        """TDCA-KG-001 §5.3 查询 1：开发角色需要哪些制度原理"""
        query = """
        MATCH (role:AgentRole {role_id: $role_id})-[:REQUIRES]->(p:Principle)
        RETURN p.id AS id, p.name AS name, p.priority AS priority,
               p.formalization AS formalization
        ORDER BY p.priority DESC
        """
        rows = self._run_all(query, {"role_id": role_id})
        self._record_nca("GetRequiredPrinciples", {"role_id": role_id}, rows)
        return rows

    # ---- 查询 2：原理矛盾检测 ----

    def detect_principle_contradictions(self, required_principles: List[str]) -> List[Dict]:
        """TDCA-KG-001 §5.3 查询 2：制度原理之间是否存在矛盾"""
        query = """
        MATCH (p1:Principle)-[:CONTRADICTS]->(p2:Principle)
        WHERE p1.id IN $required AND p2.id IN $required
        RETURN p1.id AS p1_id, p2.id AS p2_id, "CONTRADICTION_DETECTED" AS alert
        """
        rows = self._run_all(query, {"required": required_principles})
        self._record_nca("DetectPrincipleContradictions",
                         {"required": required_principles}, rows)
        return rows

    # ---- 查询 3：NSFL 规则查询 ----

    def get_nsfl_rules_for_role(self, role_id: str) -> List[Dict]:
        """TDCA-KG-001 §5.3 查询 3：开发该角色需遵守的 NSFL 规则"""
        query = """
        MATCH (role:AgentRole {role_id: $role_id})-[:MUST_OBEY]->(n:NSFLRule)
        RETURN n.id AS id, n.type AS type, n.pattern AS pattern, n.level AS level
        """
        rows = self._run_all(query, {"role_id": role_id})
        self._record_nca("GetNSFLRulesForRole", {"role_id": role_id}, rows)
        return rows

    # ---- 查询 4：函数语料六要素完整性 ----

    def verify_function_spec_completeness(self, role_id: str) -> Dict[str, bool]:
        """TDCA-KG-001 §5.3 查询 4：函数语料六要素是否完整"""
        query = """
        MATCH (role:AgentRole {role_id: $role_id})-[:DEFINED_BY]->(fs:FunctionSpec)
        RETURN
            fs.objective IS NOT NULL AS has_objective,
            fs.constraints IS NOT NULL AS has_constraints,
            fs.prior IS NOT NULL AS has_prior,
            fs.config_right IS NOT NULL AS has_config_right,
            fs.allocation IS NOT NULL AS has_allocation,
            fs.audit_trail IS NOT NULL AS has_audit_trail
        """
        record = self._run_single(query, {"role_id": role_id}) or {}
        result = {k: bool(v) for k, v in record.items()}
        self._record_nca("VerifyFunctionSpecCompleteness", {"role_id": role_id}, result)
        return result

    # ---- 查询 5：负空间事件检测 ----

    def verify_nsfl_on_path(self, dev_role: str, target_role: str) -> List[Dict]:
        """TDCA-KG-001 §5.3 查询 5：开发路径上是否存在负空间事件"""
        query = """
        MATCH path = (dev:AgentRole {role_id: $dev_role})-[:COMPILES_TO]->
                     (role:AgentRole {role_id: $target_role})
        WITH relationships(path) AS rels
        UNWIND rels AS rel
        WHERE rel.nsfl_triggered = true
        RETURN rel.nsfl_rule_id AS rule_id, rel.timestamp AS timestamp,
               "NEGATIVE_SPACE_ON_PATH" AS alert
        """
        rows = self._run_all(query, {"dev_role": dev_role, "target_role": target_role})
        self._record_nca("VerifyNSFLOnPath",
                         {"dev_role": dev_role, "target_role": target_role}, rows)
        return rows

    # ---- MRCR 场景隔离 ----

    def check_mrcr_isolation(self, agent_id: str, scene_ids: List[str]) -> bool:
        """规则 3：MRCR 场景隔离检查 — TDCA-KG-001 §2.3 / ID54"""
        query = """
        MATCH (a:AgentRole {agent_id: $agent_id})-[:HOLDS_ROLE]->(s1:Scene)
        WITH a, collect(s1.scene_id) AS roles
        WHERE size(roles) > 1
        RETURN NOT ANY(s IN roles WHERE s IN $excluded_pairs) AS isolated
        """
        record = self._run_single(query, {
            "agent_id": agent_id,
            "excluded_pairs": scene_ids,
        })
        isolated = bool((record or {}).get("isolated", True))
        self._record_nca("CheckMRCRIsolation",
                         {"agent_id": agent_id, "scene_ids": scene_ids}, {"isolated": isolated})
        return isolated

    # ---- 版本差异（OTA 支持，M4）----

    def get_version_diff(self, from_version: str,
                         to_version: str) -> List[str]:
        """
        图版本差异查询 — TDCA-KG-001 §3.4 GetGraphVersionDiff
        返回两个版本间变更的节点 ID 列表（供 gRPC VersionDiff）
        """
        if self.ota is not None and hasattr(self.ota, "diff"):
            diff = self.ota.diff(from_version, to_version)
            self._record_nca("GetGraphVersionDiff",
                             {"from": from_version, "to": to_version},
                             {"changed": len(diff["changed_nodes"])})
            return diff["changed_nodes"]
        # 无 OTA 控制器时降级为空
        self._record_nca("GetGraphVersionDiff",
                         {"from": from_version, "to": to_version}, {})
        return []

    # ---- 内部工具 ----

    def _run_single(self, query: str, params: Dict) -> Optional[Dict]:
        """执行单条记录查询（真实驱动或内存驱动）"""
        if hasattr(self.driver, "run_single"):
            return self.driver.run_single(query, params)
        with self.driver.session() as session:
            result = session.run(query, params)
            record = result.single()
            return record.data() if record else None

    def _run_all(self, query: str, params: Dict) -> List[Dict]:
        """执行多条记录查询（真实驱动或内存驱动）"""
        if hasattr(self.driver, "run_all"):
            return self.driver.run_all(query, params)
        with self.driver.session() as session:
            result = session.run(query, params)
            return [r.data() for r in result]

    def _record_nca(self, query_type: str, parameters: Dict,
                    result_summary: Any) -> Optional[str]:
        """生成查询 NCA — ID91（fail-closed：无 NCA 生成器即拒绝执行，AGENT-DEPLOY-001-FOLLOWUP TASK-006）
        六要素: 目标=查询动作 NCA 审计轨迹 / 约束=ID91 所有操作必须生成 NCA / 先验=generator 接口
        配置权边界=仅审计写入 / 预期分配=NCA 引用 / 审计轨迹=本调用"""
        if self.nca is None:
            raise NCAGenerationFailure(
                "[FAIL-CLOSED] 操作被拒绝：NCA 生成器未配置。ID91 要求所有操作必须生成 NCA。")
        if hasattr(self.nca, "record_query"):
            return self.nca.record_query(
                query_type=query_type,
                parameters=parameters,
                result_summary=result_summary,
            )
        if hasattr(self.nca, "generate"):
            nca = self.nca.generate(
                type="COGNITIVE",
                layer=1,
                parent_nca=None,
                content={"query": query_type, "params": parameters},
            )
            return getattr(nca, "nca_id", None) or getattr(nca, "id", None)
        raise NCAGenerationFailure(
            "[FAIL-CLOSED] NCA 生成器缺少 record_query/generate 接口，无法满足 ID91。")
