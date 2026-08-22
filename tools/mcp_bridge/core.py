# FC-ID: DCD-MCP-BRIDGE-001 | 模块 5 TDCA_CORE 基协议加载（接入即加载，SOUL 硬化）
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent

# 基协议指针（指针版公开口径：列纲 + 编号，全文治理条款保留）
CORE_POINTERS = {
    "TDCA-CONST": "宪法（主权信用三锚：e-CNY 唯一结算 / 税收效用锚 / 版权链·天平链权利锚）",
    "NSFL-V0.2": "负空间函数语言（不发币/不公售/不承诺分红/不代币化）",
    "TDCA-WORKING-SPEC-001": "开发工作规范（六要素/NCA 存证/数据性质标注 ID92）",
    "TDCA-OPC-COMMUNITY-001": "社区方案（缔约者网络）",
}


def load_core() -> dict:
    """加载 TDCA_CORE 基协议声明——接入 bridge 的智能体须知晓的制度底座。"""
    license_note = ""
    lic = _REPO / "LICENSE"
    if lic.is_file():
        license_note = lic.read_text(encoding="utf-8").splitlines()[0]
    return {
        "core_id": "TDCA_CORE",
        "protocols": CORE_POINTERS,
        "license_note": license_note,
        "mode": "simulated（制度演示态，ID92）",
        "hard_rules": ["不发币", "不公售", "不承诺分红", "不代币化", "不拉踩其他协议"],
    }
