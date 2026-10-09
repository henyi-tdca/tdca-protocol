# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-SBX-OPS-001（M1 核心引擎原型）
# 目标函数:     沙盒数据 + NCA 存证存储层（JSON 文件，测试隔离可注入）
# 约束矩阵:     FC-SBX-OPS-001 SV-7（存证不可篡改）+ 工作规范 §3.2（测试隔离）
# 先验分布:     NS-OPS store.py 模式（_DATA_DIR/_NCA_DIR 可注入）
# 配置权边界:    L2 层；文件存储，生产可替换
# 预期分配:     沙盒 CRUD 读写 + NCA 目录管理；失败=IOError
# 审计轨迹:      TDCA-NCA-{YYYYMMDD}-{SEQ}
# 开发者:       人类裁决 A（TDCA-FC-SBX-OPS-001）| 执行: Reasonix
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================

"""SBX-OPS M1 存储层。

制度锚定: FC-SBX-OPS-001 | SPDX-License-Identifier: TDCA-Internal

模块级 _DATA_DIR/_NCA_DIR 可被测试 conftest 注入（确定性隔离，防跨文件污染）。
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Sandbox

# 沙盒 ID 白名单（路径穿越防护: ../ 拒绝；公开常量供路由层复用，WARN-2 修复）
SANDBOX_ID_RE = re.compile(r"^did:tdca:sandbox:[0-9a-f]{32}$")
_SANDBOX_ID_RE = SANDBOX_ID_RE  # 内部别名（既有引用兼容）


def is_valid_sandbox_id(sandbox_id: str) -> bool:
    """公开校验：沙盒 ID 合法性（路径穿越防护，供路由层复用）。

    六要素声明:
    目标函数: 沙盒 ID 白名单校验（路径穿越防护）
    约束矩阵: 输入——sandbox_id；输出——bool；禁止——无
    先验分布: SANDBOX_ID_RE
    配置权边界: L2；只读校验
    预期分配: 返回是否合法；失败=无
    审计轨迹: 只读
    """
    return bool(SANDBOX_ID_RE.match(sandbox_id or ""))

_DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
_NCA_DIR: Path = Path(__file__).resolve().parent.parent / "nca"


def _ensure_dirs() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _NCA_DIR.mkdir(parents=True, exist_ok=True)


def new_sandbox_id() -> str:
    """生成沙盒 DID 标识: did:tdca:sandbox:{uuid}（任务书 §3.2）。

    六要素声明:
    目标函数: 生成唯一沙盒标识
    约束矩阵: 输入——无；输出——did:tdca:sandbox:{uuid}；禁止——重复
    先验分布: 任务书 §3.2
    配置权边界: L2
    预期分配: 返回唯一 id；失败=无
    审计轨迹: 随创建 NCA 存证
    """
    return f"did:tdca:sandbox:{uuid.uuid4().hex}"


def _sandbox_path(sandbox_id: str) -> Path:
    if not _SANDBOX_ID_RE.match(sandbox_id or ""):
        raise ValueError(f"非法沙盒 ID（路径穿越防护）: {sandbox_id!r}")
    return _DATA_DIR / f"{sandbox_id.replace(':', '_')}.json"


def save_sandbox(sandbox: Sandbox) -> None:
    """持久化沙盒（覆盖同 id）。

    六要素声明:
    目标函数: 沙盒落盘（F1-CRU 持久化）
    约束矩阵: 输入——Sandbox；输出——JSON 文件；禁止——None 入参
    先验分布: NS-OPS store 模式
    配置权边界: L2
    预期分配: 写盘成功；失败=IOError
    审计轨迹: NCA 由调用方操作先行存证
    """
    _ensure_dirs()
    _sandbox_path(sandbox.sandbox_id).write_text(
        json.dumps(sandbox.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_sandbox(sandbox_id: str) -> Optional[Sandbox]:
    """按 id 读取沙盒；不存在返回 None。

    六要素声明:
    目标函数: 沙盒读取（F1-R）
    约束矩阵: 输入——sandbox_id；输出——Sandbox|None；禁止——无
    先验分布: JSON 文件存储
    配置权边界: L2
    预期分配: 返回沙盒或 None；失败=IOError
    审计轨迹: 读取为只读，不生成 NCA
    """
    path = _sandbox_path(sandbox_id)
    if not path.exists():
        return None
    return Sandbox.model_validate(json.loads(path.read_text(encoding="utf-8")))


def list_sandboxes() -> List[Sandbox]:
    """列出全部沙盒（按创建时间升序）。

    六要素声明:
    目标函数: 沙盒列表（F1-R）
    约束矩阵: 输入——无；输出——Sandbox[]；禁止——损坏文件阻断全量
    先验分布: JSON 文件存储
    配置权边界: L2
    预期分配: 返回列表；失败=单文件损坏跳过（容错）
    审计轨迹: 只读，不生成 NCA
    """
    _ensure_dirs()
    items = []
    for p in sorted(_DATA_DIR.glob("did_tdca_sandbox_*.json"), key=lambda x: x.stat().st_mtime):
        try:
            items.append(Sandbox.model_validate(json.loads(p.read_text(encoding="utf-8"))))
        except Exception:  # noqa: BLE001 - 单文件损坏不阻断全量
            continue
    return items


def delete_sandbox_file(sandbox_id: str) -> bool:
    """物理删除沙盒文件（仅测试用；生产关闭即审计归档，不物理删除）。

    六要素声明:
    目标函数: 测试用物理删除
    约束矩阵: 输入——sandbox_id；输出——bool；禁止——生产环境调用
    先验分布: 测试隔离需求
    配置权边界: L2；仅测试
    预期分配: 删除成功返回 True；失败=文件不存在返回 False
    审计轨迹: 测试动作，不入 NCA 链
    """
    path = _sandbox_path(sandbox_id)
    if path.exists():
        path.unlink()
        return True
    return False


def count_sandboxes() -> int:
    """沙盒数量（种子幂等判断用）。

    六要素声明:
    目标函数: 计数沙盒（seed 幂等）
    约束矩阵: 输入——无；输出——int；禁止——无
    先验分布: list_sandboxes
    配置权边界: L2
    预期分配: 返回数量；失败=无
    审计轨迹: 只读
    """
    return len(list_sandboxes())
