# -*- coding: utf-8 -*-
"""
TDCANCAGenerator — 符合 TDCA-MEMO-006 附录 C 规范的 NCA 生成器

NSFL-Declaration: 生成新代码文件，不修改现有数据，不触及 ⊗ 禁止操作符
SPDX-License-Identifier: TDCA-Internal
"""

import os
import hashlib
from datetime import datetime, timezone
from typing import Optional

# PyYAML 依赖 — 安装命令: pip install pyyaml
try:
    import yaml
except ImportError:
    yaml = None  # 运行时延迟检查


class TDCANCAGenerator:
    """
    TDCA Nested Cognitive Asset Generator
    
    输入: 操作类型、文件路径、前后状态哈希
    输出: YAML 格式 NCA 文件，符合 MEMO-006 附录 C 规范
    """

    # 有效操作类型枚举
    VALID_OPERATIONS = {
        'FileMove', 'FileEdit', 'FileCreate', 'FileDelete',
        'CodeGen', 'DirCreate', 'DirMove', 'ProtocolInit',
        'ConfigChange', 'Review', 'Audit'
    }

    def __init__(
        self,
        operation_type: str,
        path: str,
        pre_state_hash: str,
        post_state_hash: str,
        operator: str = 'Reasonix',
        function_call_id: Optional[str] = None,
        nca_dir: Optional[str] = None,
        granted_by: str = 'TDCA-MEMO-006',
        scope: Optional[str] = None,
        rollback: Optional[str] = None,
        audit_trail: Optional[str] = None,
        human_signature_required: bool = True,
        max_retry: int = 0
    ):
        # NSFL 检查：操作类型合法性
        if operation_type not in self.VALID_OPERATIONS:
            raise ValueError(
                f"[NSFL-TRIGGER] 无效操作类型: {operation_type}. "
                f"有效类型: {sorted(self.VALID_OPERATIONS)}"
            )

        # PyYAML 运行时检查
        if yaml is None:
            raise ImportError(
                "[NSFL-TRIGGER] PyYAML 未安装，请执行: pip install pyyaml"
            )

        self.operation_type = operation_type
        self.path = os.path.abspath(path)
        self.pre_state_hash = pre_state_hash
        self.post_state_hash = post_state_hash
        self.operator = operator
        self.function_call_id = function_call_id or f"TDCA-FC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-001"
        # 修订项2: 时间戳固化
        self.timestamp = datetime.now(timezone.utc)
        self.nca_dir = nca_dir or os.path.join(
            os.path.dirname(os.path.dirname(self.path)) if os.path.isfile(self.path) else self.path,
            '.tdca-nca'
        ) if os.path.exists(os.path.dirname(self.path)) else os.path.join(
            os.path.expanduser('~'), '.tdca-nca'
        )
        self.granted_by = granted_by
        self.scope = scope or f"操作路径: {self.path}"
        # 修订项3: 配置权完整字段
        self.rollback = rollback or "回退至上一次通过版本"
        self.audit_trail = audit_trail or "NCA 文件记录"
        self.human_signature_required = human_signature_required
        self.max_retry = max_retry

    # ---- 核心方法 ----

    def generate(self) -> str:
        """生成 NCA YAML 文件，返回文件路径"""
        self._ensure_nca_dir()
        record = self._build_record()
        yaml_path = self._write_yaml(record)
        self._verify_yaml(yaml_path, record)
        return yaml_path

    # ---- 内部方法 ----

    def _ensure_nca_dir(self):
        """确保 NCA 存储目录存在"""
        os.makedirs(self.nca_dir, exist_ok=True)
        scripts_dir = os.path.join(self.nca_dir, 'scripts')
        os.makedirs(scripts_dir, exist_ok=True)

    def _build_record(self) -> dict:
        """构建符合 MEMO-006 附录 C 规范的 NCA 记录"""
        date_str = self.timestamp.strftime('%Y%m%d')
        # 修订项4: 使用 self.operator 去硬编码 "REASONIX"
        prefix = f"TDCA-{self.operator.upper()}"
        seq = self._next_sequence(date_str, prefix) if self._nca_dir_has_files() else 1
        nca_id = f"{prefix}-{date_str}-{seq:03d}"

        record = {
            # NCA 标识（修订项4: 动态前缀）
            'NCA-ID': nca_id,
            'Function-Call-ID': self.function_call_id,
            'Operation-Type': self.operation_type,
            'Operator': self.operator,
            # 修订项2: 使用固化的 self.timestamp
            'Timestamp': self.timestamp.isoformat(),
            'Scope': self.scope,

            # 操作前后状态
            'Pre-State': {
                'Path': self.path,
                'Hash': self.pre_state_hash,
                'Size': self._get_size(self.path) if os.path.exists(self.path) else 0
            },
            'Post-State': {
                'Path': self.path,
                'Hash': self.post_state_hash,
                'Size': self._get_size(self.path) if os.path.exists(self.path) else 0
            },

            # 修订项3: 配置权边界完整 6 字段
            'Config-Right-Token': {
                'Scope': self.scope,
                'Rollback': self.rollback,
                'Audit-Trail': self.audit_trail,
                'Human-Signature-Required': self.human_signature_required,
                'Max-Retry': self.max_retry,
                'Granted-By': self.granted_by,
                'Expires': None
            },

            # 审计轨迹
            'Audit-Trail': [
                {'Step': f"操作执行: {self.operation_type}",
                 'Time': self.timestamp.isoformat(),
                 'Evidence': self.post_state_hash}
            ],

            # 人类签名（待审批）
            'Human-Signature': {
                'Status': 'Pending',
                'Signed-By': None,
                'Signed-At': None
            },

            # 负空间检查
            'Negative-Space-Check': {
                'NSFL-Version': 'V0.2',
                'Triggered': False,
                'Trigger-Reason': None
            }
        }
        return record

    def _write_yaml(self, record: dict) -> str:
        """将 NCA 记录写入 YAML 文件（PyYAML 实现）"""
        nca_filename = f"NCA-{record['NCA-ID']}.yaml"
        nca_path = os.path.join(self.nca_dir, nca_filename)
        with open(nca_path, 'w', encoding='utf-8') as f:
            yaml.dump(record, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        return nca_path

    def _verify_yaml(self, yaml_path: str, original: dict):
        """验证 YAML 写入完整性（PyYAML 解析）"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        required_fields = [
            'NCA-ID', 'Function-Call-ID', 'Operation-Type', 'Operator',
            'Timestamp', 'Pre-State', 'Post-State', 'Config-Right-Token',
            'Audit-Trail', 'Human-Signature', 'Negative-Space-Check'
        ]
        for field in required_fields:
            if field not in loaded:
                raise ValueError(f"[NSFL-TRIGGER] NCA 字段缺失: {field}")
        # 验证 NCA-ID 一致性
        assert loaded['NCA-ID'] == original['NCA-ID'], "NCA-ID 不匹配"
        print(f"[OK] NCA 验证通过: {yaml_path}")

    def _next_sequence(self, date_str: str, prefix: str) -> int:
        """计算当日下一个序列号"""
        existing = [f for f in os.listdir(self.nca_dir)
                    if f.startswith(f'NCA-{prefix}-{date_str}') and f.endswith('.yaml')]
        return len(existing) + 1

    def _nca_dir_has_files(self) -> bool:
        """检查 NCA 目录是否已有文件"""
        return os.path.isdir(self.nca_dir) and len(os.listdir(self.nca_dir)) > 0

    @staticmethod
    def _get_size(path: str) -> int:
        """获取文件大小"""
        try:
            return os.path.getsize(path)
        except OSError:
            return 0

    # ---- 工具方法 ----

    @staticmethod
    def hash_file(path: str) -> str:
        """计算文件 SHA-256 哈希"""
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """计算字节数据 SHA-256 哈希"""
        return hashlib.sha256(data).hexdigest()


# ---- 命令行入口 ----
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 4:
        print("用法: python tdca_nca_generator.py <操作类型> <文件路径> <前哈希> [后哈希] [操作者]")
        print(f"操作类型: {sorted(TDCANCAGenerator.VALID_OPERATIONS)}")
        sys.exit(1)

    op_type = sys.argv[1]
    path = sys.argv[2]
    pre_hash = sys.argv[3]
    post_hash = sys.argv[4] if len(sys.argv) > 4 else pre_hash
    operator = sys.argv[5] if len(sys.argv) > 5 else 'Reasonix'

    gen = TDCANCAGenerator(
        operation_type=op_type,
        path=path,
        pre_state_hash=pre_hash,
        post_state_hash=post_hash,
        operator=operator
    )
    result = gen.generate()
    print(f"[OK] NCA 已生成: {result}")
