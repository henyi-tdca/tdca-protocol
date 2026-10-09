# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-NS-OPS-001（M3 验收交付）
# 目标函数:     测试隔离统一管理（REV-#9）——autouse fixture 重置测试数据目录
# 约束矩阵:     M1/M2/M3 测试互不污染（确定性回归）
# 先验分布:     pytest fixture 机制
# 配置权边界:    L2 层；仅测试环境
# 预期分配:     每测试独立数据目录；失败=断言异常
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（DCD-NS-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.1
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""测试隔离统一管理（REV-#9）。

制度锚定: FC-NS-OPS-001 M3 | SPDX-License-Identifier: TDCA-Internal
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

import app.store as store  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_store():
    """每个测试用例独立数据/NCA 目录（确定性隔离，防跨文件污染）+ 种子初始化。"""
    data_dir = _BACKEND / "data_test"
    nca_dir = _BACKEND / "nca_test"
    # 清空并重置
    for d in (data_dir, nca_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)
    store._DATA_DIR = data_dir  # type: ignore[attr-defined]
    store._NCA_DIR = nca_dir  # type: ignore[attr-defined]
    # 种子幂等初始化（三层负空间 6 条演示数据）
    from app.seed import seed_if_empty

    seed_if_empty()
    yield
    # 用例后清理
    for d in (data_dir, nca_dir):
        if d.exists():
            shutil.rmtree(d)
