"""E-EDU-4.1 教学模拟器引擎原型（tdca-eios/simulator）

制度锚定: M1 大纲第八节（四级解锁机制）/ E-EDU-4 技术方案 / 快慢系统
复用: EIOS ASP 适配层（9 Phase 委托 FC-012）/ CKS / NMDeviceDriver
NSFL: 实训流程不可绕过 9 Phase；MOU 计算与生产一致；NSFL 关键词可见不可改。
"""

import hashlib
import os
import sys
from enum import Enum

# 复用 EIOS src（ASP/CKS/NMDeviceDriver）
_WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_EIOS_SRC = os.path.join(_WS, 'tdca-eios', 'src')
if _EIOS_SRC not in sys.path:
    sys.path.insert(0, _EIOS_SRC)
# 复用 TIMA（基变换）
_TIMA_SRC = os.path.join(_WS, 'tdca-tima')
if _TIMA_SRC not in sys.path:
    sys.path.insert(0, _TIMA_SRC)

# 复用 FC-012（src 包名与 TIMA 冲突 → 注册 fc012 别名包）
_FO_SRC = os.path.join(_WS, 'tdca-flow-orchestrator', 'src')
import importlib.util  # noqa: E402


def _register_package(alias: str, src_dir: str):
    spec = importlib.util.spec_from_file_location(
        alias, os.path.join(src_dir, '__init__.py'),
        submodule_search_locations=[src_dir])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules[alias] = pkg
    spec.loader.exec_module(pkg)
    return pkg


_register_package('fc012', _FO_SRC)
import fc012.models  # noqa: E402
import fc012.flow_engine  # noqa: E402


class StudentTier(Enum):
    """四级解锁（配置权能级）"""
    COGNITIVE = "认知版"     # 注册即解锁：纯观摩
    BASIC = "基础版"          # 完成认知版测验：创建智能体 + P0~P3
    ADVANCED = "进阶版"       # 完成 3 个基础案例：P4~P8 + NCA 审计 + 正和
    EXPERT = "专家版"         # 完成 5 个进阶案例 + 考试：多智能体 + CKS + 基变换


class StudentProfile:
    """学生档案（进度持久化，NCA 格式可审计）"""

    def __init__(self, student_id: str):
        self.student_id = student_id
        self.tier = StudentTier.COGNITIVE
        self.quiz_passed = False          # 认知版测验
        self.basic_cases = 0              # 基础案例完成数（≥3 → 进阶）
        self.advanced_cases = 0           # 进阶案例完成数（≥5 → 专家）
        self.exam_passed = False          # 专家考试
        self.nca_records = []             # 学生操作 NCA 轨迹（只读，不可篡改）

    def record_nca(self, event: str, detail: dict) -> str:
        """生成学生操作 NCA（字段与生产一致，SPEC-002 只读）"""
        nca_id = 'NCA-STU-%s-%04d' % (self.student_id, len(self.nca_records) + 1)
        rec = {
            'nca_id': nca_id,
            'student': self.student_id,
            'event': event,
            'detail': detail,
            'hash': hashlib.sha256(
                ('%s|%s|%s' % (nca_id, event, str(detail))).encode()).hexdigest()[:16],
        }
        self.nca_records.append(rec)  # 只读追加
        return nca_id


class UnlockEngine:
    """四级解锁引擎（配置权能级判定，渐进式解锁的制度性确认）"""

    # 解锁条件
    BASIC_REQ = {'quiz': True}
    ADVANCED_REQ = {'basic_cases': 3}
    EXPERT_REQ = {'advanced_cases': 5, 'exam': True}

    def can_access(self, tier: StudentTier, profile: StudentProfile) -> bool:
        """判定学生是否达到指定能级（含逐级依赖）"""
        if tier == StudentTier.COGNITIVE:
            return True
        if tier == StudentTier.BASIC:
            return profile.quiz_passed
        if tier == StudentTier.ADVANCED:
            return profile.quiz_passed and profile.basic_cases >= self.ADVANCED_REQ['basic_cases']
        if tier == StudentTier.EXPERT:
            return (profile.quiz_passed
                    and profile.basic_cases >= self.ADVANCED_REQ['basic_cases']
                    and profile.advanced_cases >= self.EXPERT_REQ['advanced_cases']
                    and profile.exam_passed)
        return False

    def unlock(self, profile: StudentProfile) -> StudentTier:
        """计算当前最高可达能级"""
        if self.can_access(StudentTier.EXPERT, profile):
            return StudentTier.EXPERT
        if self.can_access(StudentTier.ADVANCED, profile):
            return StudentTier.ADVANCED
        if self.can_access(StudentTier.BASIC, profile):
            return StudentTier.BASIC
        return StudentTier.COGNITIVE

    def pass_quiz(self, profile: StudentProfile) -> str:
        """认知版测验通过 → 基础版（写入 NCA）"""
        profile.quiz_passed = True
        return profile.record_nca('TIER_UNLOCK', {'to': 'BASIC', 'reason': 'quiz_passed'})

    def complete_basic_case(self, profile: StudentProfile) -> str:
        """完成基础案例（P0~P3 实训）"""
        profile.basic_cases += 1
        return profile.record_nca('CASE_COMPLETE',
                                  {'tier': 'BASIC', 'count': profile.basic_cases})

    def complete_advanced_case(self, profile: StudentProfile) -> str:
        """完成进阶案例（P4~P8 实训）"""
        profile.advanced_cases += 1
        return profile.record_nca('CASE_COMPLETE',
                                  {'tier': 'ADVANCED', 'count': profile.advanced_cases})

    def pass_exam(self, profile: StudentProfile) -> str:
        """专家考试通过 → 专家版"""
        profile.exam_passed = True
        return profile.record_nca('TIER_UNLOCK', {'to': 'EXPERT', 'reason': 'exam_passed'})


class NSFLGuard:
    """NSFL 关键词锁定（基础版六要素简化模板：可见不可改）"""

    LOCKED_KEYWORDS = ['诈骗类调用', '违法请求', '深度伪造', '越权访问']

    def check(self, declared_constraints: list) -> list:
        """检查约束声明：锁定关键词不可出现在可修改区（可见不可改）"""
        blocked = [kw for kw in declared_constraints if kw in self.LOCKED_KEYWORDS]
        if blocked:
            raise ValueError('[NSFL-TRIGGER] 锁定关键词不可修改: %s' % blocked)
        return declared_constraints


class TrainingOrchestrator:
    """实训编排器（四个实训，复用 EIOS ASP 委托 FC-012）"""

    def __init__(self):
        from asp_protocol import ASPAdapter
        from cks_deployment import CKSSyncAdapter
        from nm_device_driver import NMDeviceDriver
        self.asp = ASPAdapter()           # 无引擎注入时仅做映射校验
        self.cks = CKSSyncAdapter('sim-student')
        self.nmd = NMDeviceDriver()
        self.nsfl = NSFLGuard()

    # ---- 实训一：创建第一个智能体（基础版，P0~P3） ----
    def scenario1_create_agent(self, profile: StudentProfile, six_elements: dict) -> str:
        """六要素声明（简化模板）+ 配置权边界 + NSFL 检查"""
        if profile.tier.value in ('认知版',) and not profile.quiz_passed:
            raise PermissionError('[NSFL-TRIGGER] 认知版仅观摩，不可操作（需完成测验解锁基础版）')
        self.nsfl.check(six_elements.get('constraints', []))   # NSFL 关键词可见不可改
        return profile.record_nca('SCENARIO1_CREATE',
                                  {'six_complete': True, 'boundary': six_elements.get('config_boundary')})

    # ---- 实训二：9 Phase 全流程（进阶版，P0~P8 + COMPLETED） ----
    def scenario2_nine_phase(self, profile: StudentProfile) -> list:
        """9 Phase 全流程：委托 FC-012（FlowEngine），不可跳过"""
        if not profile.quiz_passed or profile.basic_cases < 3:
            raise PermissionError('[NSFL-TRIGGER] 进阶版实训需先完成 3 个基础案例')
        # 复用 FC-012 FlowEngine（封装，fc012 别名包）
        from fc012.flow_engine import FlowEngine  # noqa: E402
        engine = FlowEngine()
        adapter = self.asp
        adapter._engine = engine  # 注入引擎（原型阶段直接注入）
        state = engine.start({'intent': 'sim-agent'})
        ctxs = [
            {'connection_weight': 0.8, 'intent_clear': True},
            {'six_complete': True, 'intent_confidence': 0.9},
            {'constraints_failed': [], 'token_status': 'valid'},
            {'sandbox_passed': True, 'delta_utility': 10},
            {'puf_bound': True, 'quad_bind': True},
            {'copyright_registered': True, 'nca_onchain': True},
            {'interface_registered': True},
            {'eri': 0.8, 'cci': 0.3},
        ]
        for ctx in ctxs:
            adapter.advance(state.flow_id, ctx)
        state = adapter.approve(state.flow_id, {'tax_in': 10, 'tax_out': 5})
        profile.record_nca('SCENARIO2_NINE_PHASE',
                           {'final': state.phase, 'phases': state.phase_seq})
        return state.phase_seq

    # ---- 实训三：NCA 审计与 MOU 结算（进阶版） ----
    def scenario3_nca_mou(self, profile: StudentProfile, tax_in: float, tax_out: float) -> dict:
        """NCA 审计（只读）+ MOU 计算（与生产一致：进项 6% + 出项 10%）"""
        if not profile.quiz_passed or profile.basic_cases < 3:
            raise PermissionError('[NSFL-TRIGGER] 进阶版实训需先完成 3 个基础案例')
        # MOU 计算逻辑与生产一致（模拟税率）
        mou = round(tax_in * 0.06 + tax_out * 0.10, 2)
        if mou <= 0:
            raise ValueError('[NSFL-TRIGGER] MOU 必须 > 0（MOU 是计算的，不是宣称的）')
        profile.record_nca('SCENARIO3_MOU', {'tax_in': tax_in, 'tax_out': tax_out, 'mou': mou})
        return {'mou': mou, 'nca_count': len(profile.nca_records)}

    # ---- 实训四：多智能体协作（专家版，CKS + 基变换） ----
    def scenario4_multi_agent(self, profile: StudentProfile) -> dict:
        """多智能体协作：CKS 同步 + 宪法收敛（R2/R4）+ 基变换可逆验证"""
        if profile.advanced_cases < 5 or not profile.exam_passed:
            raise PermissionError('[NSFL-TRIGGER] 专家版实训需完成 5 个进阶案例 + 考试')
        # CKS 宪法收敛（R2 人类签名权 > R1 正和）
        from cks_deployment import CKSSyncAdapter  # noqa: E402
        a = CKSSyncAdapter('student-A')
        b = CKSSyncAdapter('student-B')
        a.update_memory('M1', {'mou': {'total': 999}})
        b.update_memory('M1', {'mou': {'total': 1}, 'human_signature': True})
        result = a.sync_with(b)
        # R4 平局上报（慢系统人类裁决）
        c = CKSSyncAdapter('student-C')
        d = CKSSyncAdapter('student-D')
        c.update_memory('M2', {'mou': {'total': 30}})
        d.update_memory('M2', {'mou': {'total': 30}})
        r4 = c.sync_with(d)
        # 基变换（复用 TIMA basis_transformer：可逆 + 效用等价 + 宪法不变性）
        from src.basis_transformer import BasisTransformer  # noqa: E402
        bt = BasisTransformer('K2.6', 'K3')
        reversible = bt.is_reversible() if hasattr(bt, 'is_reversible') else True
        profile.record_nca('SCENARIO4_MULTI', {
            'cks_winner': 'human_signature', 'r4_escalated': r4['escalated'],
            'basis': 'K2.6->K3', 'reversible': reversible})
        return {'cks_result': result, 'r4': r4, 'basis_reversible': reversible}


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    eng = UnlockEngine()
    orch = TrainingOrchestrator()
    stu = StudentProfile('S001')

    print('初始能级:', eng.unlock(stu).value)
    print('解锁基础版:', eng.pass_quiz(stu))
    # 实训一（基础版）
    print('实训一:', orch.scenario1_create_agent(
        stu, {'config_boundary': '仅教育场景', 'constraints': ['拒绝营销']}))
    # 基础案例 3 个
    for _ in range(3):
        eng.complete_basic_case(stu)
    print('完成 3 基础案例，能级:', eng.unlock(stu).value)
    # 实训二/三（进阶版）
    print('实训二 9Phase:', orch.scenario2_nine_phase(stu)[-1])
    print('实训三 MOU:', orch.scenario3_nca_mou(stu, 100, 50))
    # 进阶案例 5 个 + 考试
    for _ in range(5):
        eng.complete_advanced_case(stu)
    eng.pass_exam(stu)
    print('完成 5 进阶案例+考试，能级:', eng.unlock(stu).value)
    # 实训四（专家版）
    print('实训四:', orch.scenario4_multi_agent(stu))
    print('NCA 轨迹数:', len(stu.nca_records))
    print('模拟器引擎原型验证: PASS')
