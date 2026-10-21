# -*- coding: utf-8 -*-
"""
TDCAConfigRightTokenGenerator — 配置权边界声明自动生成器

  衔接已归档的 TDCANCAGenerator (@ FC-001)
  每次操作前自动生成合规 Config-Right-Token
  内置 validate() 自证机制 + Token-ID 关联锚定

NSFL-Declaration: 生成新代码文件，不修改现有数据，不触及 ⊗ 禁止操作符
SPDX-License-Identifier: TDCA-Internal
"""

import os
import yaml
from datetime import datetime, timezone
from typing import Optional


class TDCAConfigRightTokenGenerator:
    """
    TDCA 配置权边界自动生成器

    根据 task_type / risk_level 自动推断权限配置，
    负空间任务自动标注 NSFL-Declaration，
    输出 Token-ID 锚定，与 TDCANCAGenerator 协同。

    修正项 P0-P2 已应用:
      - P0: 所有写操作为 Human-Signature-Required=true (仅 Review=false)
      - P1: human_override: Optional[dict] / validate()→None
      - P2: task_type 字段镜像回写
    """

    # 操作类型 → (Human-Signature-Required, Max-Retry, Rollback策略, 负空间标注)
    INFERENCE_TABLE = {
        'FileMove':   (True,  0, "路径级回退 (move back)",   "⊗ 跨域移动需路径合法性预检"),
        'FileEdit':   (True,  0, ".bak 备份恢复",            "⊗ 修改操作需基线校验"),
        'FileDelete': (True,  0, "回收站/备份恢复",          "⊗ 删除操作不可逆，请确认"),
        'FileCreate': (True,  0, "创建后删除",               ""),
        'CodeGen':    (True,  0, "删除生成文件",             ""),
        'DirCreate':  (True,  0, "删除空目录",               ""),
        'DirMove':    (True,  0, "路径级回退",               "⊗ 目录迁移需完整性校验"),
        'ProtocolInit': (True,  0, "目录级回退",             ""),
        'ConfigChange': (True,  0, "配置快照回退",           ""),
        'Review':     (False, 3, "无（只读操作）",           ""),
        'Audit':      (True,  0, "审计报告留痕",             ""),
    }

    VALID_OPERATIONS = set(INFERENCE_TABLE.keys())

    # 修正1: 负空间任务集合显性化（单一事实源，不与 INFERENCE_TABLE ⊗ 标注重复定义）
    NSFL_TASKS = {'FileDelete', 'FileEdit', 'FileMove', 'DirMove'}

    def __init__(
        self,
        task_type: str,
        target_path: str,
        operator: str = "Reasonix",
        risk_level: str = "LOW",
        human_override: Optional[dict] = None,
        description: Optional[str] = None,
        token_dir: Optional[str] = None
    ):
        # NSFL: 操作类型合法性
        if task_type not in self.VALID_OPERATIONS:
            raise ValueError(
                f"[NSFL-TRIGGER] 无效操作类型: {task_type}. "
                f"有效类型: {sorted(self.VALID_OPERATIONS)}"
            )

        self.task_type = task_type
        self.target_path = os.path.abspath(target_path)
        self.operator = operator
        self.risk_level = risk_level.upper()
        self.human_override = human_override or {}
        self.description = description or f"操作: {task_type} @ {self.target_path}"
        self.token_dir = token_dir or os.path.join(
            os.path.dirname(self.target_path) if os.path.isdir(os.path.dirname(self.target_path))
            else os.path.expanduser('~'),
            '.tdca-nca', 'tokens'
        )

    # ---- 核心方法 ----

    def generate(self) -> dict:
        """生成完整的 Config-Right-Token dict，自动调用 validate()"""
        data = self._infer()
        token = self._build_token(data)
        self.validate(token)  # P1: 不可绕过，不通过→ValueError
        return token

    def validate(self, token: dict) -> None:
        """
        自证机制：验证 Token 的字段完整性和负空间合规性。

        通过时无返回值；不通过时抛出 ValueError("[NSFL-TRIGGER] ...")。
        检查项:
          1. 6 强制字段存在且非空
          2. 负空间任务 NSFL-Declaration 不可为空
          3. 写操作 Human-Signature-Required 不可被覆盖
          4. Token-ID 格式符合 TDCA-CRT-{8位日期}-{3位序列}.yaml
        """
        errors = []

        # 1. 字段完整性（检查 8 项: Token-ID/Scope/Rollback/Audit-Trail/
        #    Human-Signature-Required/Max-Retry/Granted-By/task_type）
        required = ['Token-ID', 'Scope', 'Rollback', 'Audit-Trail',
                    'Human-Signature-Required', 'Max-Retry', 'Granted-By', 'task_type']
        for field in required:
            if field not in token or token[field] is None:
                errors.append(f"缺失字段: {field}")

        # 2. 负空间合规（修正1: 使用类常量 NSFL_TASKS）
        if token.get('task_type') in self.NSFL_TASKS:
            if not token.get('NSFL-Declaration'):
                errors.append(f"负空间任务 {token['task_type']} 需要 NSFL-Declaration")

        # 3. 签名要求不可被覆盖
        inferred_sig, _, _, _ = self.INFERENCE_TABLE[self.task_type]
        if inferred_sig is True and token.get('Human-Signature-Required') is not True:
            errors.append(f"写操作 {self.task_type} 强制 Human-Signature-Required=true")

        # 4. Token-ID 格式
        tid = token.get('Token-ID', '')
        import re
        if not re.match(r'^TDCA-CRT-\d{8}-\d{3}$', tid):
            errors.append(f"Token-ID 格式无效: {tid}")

        if errors:
            reason = '; '.join(errors)
            raise ValueError(f"[NSFL-TRIGGER] validate failed: {reason}")

    # ---- 内部方法 ----

    def _infer(self) -> dict:
        """根据 task_type 查找推断表"""
        sig, retry, rollback, nsfl = self.INFERENCE_TABLE[self.task_type]
        # 修正项 P0: risk_level=HIGH → 强制签名
        if self.risk_level == 'HIGH':
            sig = True
        return {
            'signature': sig,
            'max_retry': retry,
            'rollback': rollback,
            'nsfl': nsfl
        }

    def _build_token(self, inferred: dict) -> dict:
        """构建完整的 Token dict"""
        token = {
            'Token-ID': self._next_token_id(),
            'Scope': self.description,
            'Rollback': inferred['rollback'],
            'Audit-Trail': f"Token 由 {self.__class__.__name__} 生成于 {datetime.now(timezone.utc).isoformat()}",
            'Human-Signature-Required': inferred['signature'],
            'Max-Retry': inferred['max_retry'],
            'Granted-By': 'TDCA-MEMO-006',
            'task_type': self.task_type  # P2: 镜像回写
        }

        # 可选字段
        if inferred['nsfl']:
            token['NSFL-Declaration'] = inferred['nsfl']

        # 修正2: human_override 不可覆盖 Token-ID/Granted-By/Audit-Trail/Human-Signature-Required
        overrides = {k: v for k, v in self.human_override.items()
                     if k not in ('Human-Signature-Required', 'Token-ID', 'Granted-By', 'Audit-Trail')}
        token.update(overrides)

        return token

    def _next_token_id(self) -> str:
        """
        生成 Token-ID: TDCA-CRT-{date}-{seq:03d}

        修正3 (P3-KNOWN): 当前基于文件计数实现，多进程并发下可能冲突。
        后续方案: 引入 fcntl/portalocker 文件锁，或 UUID7 后缀作为过渡。
        """
        os.makedirs(self.token_dir, exist_ok=True)
        today = datetime.now(timezone.utc).strftime('%Y%m%d')
        existing = [f for f in os.listdir(self.token_dir)
                    if f.startswith(f'TDCA-CRT-{today}')]
        seq = len(existing) + 1
        return f"TDCA-CRT-{today}-{seq:03d}"

    # ---- 序列化 ----

    def to_yaml(self, token: dict) -> str:
        """将 Token dict 序列化为 YAML 字符串"""
        return yaml.dump(token, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)

    def save(self, token: dict) -> str:
        """保存 Token 为 YAML 文件，返回文件路径"""
        self.validate(token)  # 保存前二次验证
        os.makedirs(self.token_dir, exist_ok=True)
        filename = f"{token['Token-ID']}.yaml"
        filepath = os.path.join(self.token_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(token, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        return filepath

    @classmethod
    def load(cls, filepath: str) -> dict:
        """从 YAML 文件加载 Token"""
        with open(filepath, 'r', encoding='utf-8') as f:
            token = yaml.safe_load(f)
        inst = cls(token['task_type'], token.get('Scope', '.'))
        inst.validate(token)
        return token


# ---- CLI ----
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print(f"用法: python {sys.argv[0]} <task_type> <target_path> [risk_level] [description]")
        print(f"task_type: {sorted(TDCAConfigRightTokenGenerator.VALID_OPERATIONS)}")
        sys.exit(1)

    gen = TDCAConfigRightTokenGenerator(
        task_type=sys.argv[1],
        target_path=sys.argv[2],
        risk_level=sys.argv[3] if len(sys.argv) > 3 else 'LOW',
        description=sys.argv[4] if len(sys.argv) > 4 else None
    )
    token = gen.generate()
    print(gen.to_yaml(token))
