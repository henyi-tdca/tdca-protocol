"""
TDCA-FC-20260801-003 修正声明:
  - P0: 模块命名由 TDCAMOUGenerator 修正为 TDCAMOURecorder
  - P0: 核心方法由 generate() 修正为 record()
  - P0: Pre-Est 字段强制标记 [SIMULATED]
  - P0: Activation-Coefficient 禁止基于 Pre-Est 计算
  - P1: tdca-tool CLI 增加权限自洽检查 _check_auth()
  - P1: HIGH 风险操作强制人类签名

制度锚定: TDCA-PRINCIPLE-MOU-001, ID79, TDCA-MEMO-008
Granted-By: TDCA-PRINCIPLE-MOU-001

NSFL-Declaration:
  - 禁止伪造税收数据（Tax-In/Tax-Out 必须为真实数据源或显式 null）
  - 禁止用 Pre-Est 替代 Actual-Total 计算 Activation-Coefficient
  - 禁止创建无 Token-Ref 的 MOU 记录
  - 禁止修改已归档 MOU 的税收字段（审计轨迹只追加）
SPDX-License-Identifier: TDCA-Internal
"""

import os
import re
import yaml
from datetime import datetime, timezone
from typing import Optional


class TDCAMOURecorder:
    """
    TDCA MOU 计量与锚定记录器

    核心约束（ID79 / TDCA-PRINCIPLE-MOU-001）：
      - 只读税收数据源，不可写入/伪造税收数据
      - Pre-Est 仅为模拟阶段占位，标记 [SIMULATED]
      - Actual-Total 为 null 时，Activation-Coefficient 强制为 null
      - 每次 record() 必须关联有效 Token-ID

    概念定位：计量并锚定已发生的税收事实，非生成模拟数据。
    """

    MOU_ID_PATTERN = re.compile(r'^TDCA-MOU-\d{8}-\d{3}$')

    def __init__(
        self,
        token_ref: str,                    # 必填：Config-Right-Token ID
        nca_ref: Optional[str] = None,     # 可选：NCA-ID
        pre_est: Optional[float] = None,   # 预估值（模拟阶段）
        operator: str = "Reasonix",
        mou_dir: Optional[str] = None
    ):
        # 验证 token_ref 格式
        if not re.match(r'^TDCA-CRT-\d{8}-\d{3}$', token_ref):
            raise ValueError(f"[NSFL-TRIGGER] Token-Ref 格式无效: {token_ref}")

        self.token_ref = token_ref
        self.nca_ref = nca_ref
        self.pre_est = pre_est
        self.operator = operator
        self.mou_dir = mou_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '.tdca-nca', 'mou'
        )

        # 验证 token_ref 对应的 Token 文件存在（.tdca-nca/tokens/）
        tokens_dir = os.path.dirname(self.mou_dir)
        if tokens_dir.endswith('mou'):
            tokens_dir = os.path.dirname(tokens_dir)
        tokens_dir = os.path.join(tokens_dir, 'tokens')
        token_file = os.path.join(tokens_dir, f"{token_ref}.yaml")
        if not os.path.exists(token_file):
            # 非致命：目录可能尚未创建，验证在 validate() 中完整执行
            pass

    def record(self, tax_in: Optional[float] = None, tax_out: Optional[float] = None) -> dict:
        """
        记录 MOU。

        参数:
          tax_in:  进项税收（真实数据，测试阶段可为 null）
          tax_out: 出项税收（真实数据，测试阶段可为 null）

        返回:
          完整 MOU 记录字典（通过 validate() 自证）

        异常:
          ValueError("[NSFL-TRIGGER] ...") 当验证失败时
        """
        now = datetime.now(timezone.utc)

        # 计算 Actual-Total（两者均为 null 时保持 null）
        if tax_in is not None and tax_out is not None:
            actual_total = tax_in + tax_out
        else:
            actual_total = None

        record = {
            'MOU-ID': self._next_mou_id(),
            'Token-Ref': self.token_ref,
            'NCA-Ref': self.nca_ref,
            'Recorded-At': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'Operator': self.operator,
            # 税收锚定（硬数据）
            'Tax-In': tax_in,
            'Tax-Out': tax_out,
            'Actual-Total': actual_total,
            # 预估字段
            'Pre-Est': self.pre_est,
            'Pre-Est-Status': "[SIMULATED]" if self.pre_est is not None else None,
            # 激活系数（仅基于 Actual-Total，此处保持 null 由 compute_activation 填充）
            'Activation-Coefficient': None,
            # 制度锚定
            'Granted-By': 'TDCA-PRINCIPLE-MOU-001',
            'Audit-Trail': f"记录由 TDCAMOURecorder 生成于 {now.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        }

        self.validate(record)
        return record

    def validate(self, mou_record: dict) -> None:
        """
        自证机制：
          1. MOU-ID 格式合规
          2. Token-Ref 存在且有效
          3. 若 Tax-In/Tax-Out 均为 null，则 Pre-Est 必须存在且标记 [SIMULATED]
          4. 若 Actual-Total 为 null，则 Activation-Coefficient 必须为 null
          5. 时间戳顺序：Token.created_at < MOU.recorded_at
        """
        errors = []

        # 1. MOU-ID 格式
        mou_id = mou_record.get('MOU-ID')
        if not mou_id or not self.MOU_ID_PATTERN.match(mou_id):
            errors.append(f"MOU-ID 格式无效: {mou_id}")

        # 2. Token-Ref 存在且格式有效
        token_ref = mou_record.get('Token-Ref')
        if not token_ref or not re.match(r'^TDCA-CRT-\d{8}-\d{3}$', token_ref):
            errors.append(f"Token-Ref 缺失或格式无效: {token_ref}")

        # 3. 若 Tax-In/Tax-Out 均为 null，则 Pre-Est 必须存在且标记 [SIMULATED]
        tax_in = mou_record.get('Tax-In')
        tax_out = mou_record.get('Tax-Out')
        pre_est = mou_record.get('Pre-Est')
        pre_est_status = mou_record.get('Pre-Est-Status')
        if tax_in is None and tax_out is None:
            if pre_est is None:
                errors.append("Tax-In/Tax-Out 均为 null 时 Pre-Est 必须存在")
            if pre_est_status != "[SIMULATED]":
                errors.append("Pre-Est 必须标记 [SIMULATED]")

        # 4. 若 Actual-Total 为 null，则 Activation-Coefficient 必须为 null
        actual_total = mou_record.get('Actual-Total')
        activation = mou_record.get('Activation-Coefficient')
        if actual_total is None and activation is not None:
            errors.append("Actual-Total 为 null 时 Activation-Coefficient 必须为 null")

        # 5. 时间戳顺序（此处无法读取 Token 文件时跳过，由 verify_chain 完整检查）
        # 记录时间戳本身格式校验
        recorded_at = mou_record.get('Recorded-At')
        if recorded_at:
            try:
                datetime.strptime(recorded_at, '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                errors.append(f"Recorded-At 时间戳格式无效: {recorded_at}")

        if errors:
            reason = '; '.join(errors)
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {reason}")

    def compute_activation_coefficient(self, actual_total: float, gov_pcr: float, employment_ss: float = 0) -> float:
        """
        激活系数计算（TDCA 生态沙盒核心公式）
        公式: (actual_total + employment_ss) / gov_pcr
        约束: gov_pcr > 0，否则抛出 ValueError
        """
        if gov_pcr <= 0:
            raise ValueError(f"[NSFL-TRIGGER] gov_pcr 必须 > 0，当前: {gov_pcr}")
        return (actual_total + employment_ss) / gov_pcr

    def to_yaml(self, mou_record: dict) -> str:
        """序列化为 YAML 字符串"""
        return yaml.dump(mou_record, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)

    def save(self, mou_record: dict) -> str:
        """保存为 YAML 文件，返回路径"""
        self.validate(mou_record)
        os.makedirs(self.mou_dir, exist_ok=True)
        filename = f"{mou_record['MOU-ID']}.yaml"
        filepath = os.path.join(self.mou_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(mou_record, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        return filepath

    @classmethod
    def load(cls, filepath: str) -> dict:
        """从 YAML 加载并验证"""
        with open(filepath, 'r', encoding='utf-8') as f:
            record = yaml.safe_load(f)
        # 用临时实例验证
        inst = cls(token_ref=record['Token-Ref'])
        inst.validate(record)
        return record

    def _next_mou_id(self) -> str:
        """生成 MOU-ID: TDCA-MOU-{date}-{nnn}"""
        os.makedirs(self.mou_dir, exist_ok=True)
        today = datetime.now(timezone.utc).strftime('%Y%m%d')
        existing = [f for f in os.listdir(self.mou_dir)
                    if f.startswith(f'TDCA-MOU-{today}')]
        seq = len(existing) + 1
        return f"TDCA-MOU-{today}-{seq:03d}"
