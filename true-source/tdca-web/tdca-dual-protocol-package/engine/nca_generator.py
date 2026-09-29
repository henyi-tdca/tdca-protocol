# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# =============================================================================
# FC-ID:        TDCA-FC-20260811-002-DUAL-PROTOCOL
# 目标函数:     双协议 NCA 生成器（化合产物存证）
# 约束矩阵:     MEMO-006 附录 C 11 字段 + MOU-Anchor + NSFL-V0.2
# 先验分布:     TDCA-DUAL-PROTOCOL-001-V1.0 设计稿
# 配置权边界:    L2 配置权市场层；生成存证不执行配置权
# 预期分配:     dual-nca.json（化合 NCA 存证）
# 审计轨迹:      TDCA-NCA-20260811-006-DUAL-PROTOCOL
# 开发者:       [人类签批人]
# 模拟态标注（ID92）: 本引擎为工具实现，不构成真实配置权执行路径
# 负空间版本:     NSFL-V0.2
# MOU 锚定:      TDCA-MOU-{date}-{seq}
# =============================================================================
"""TDCA 双协议 NCA 生成器 V1.0.0

生成符合 MEMO-006 附录 C 规范的双协议化合 NCA 存证（JSON/YAML）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class DualNcaGenerator:
    """双协议化合 NCA 生成器。"""

    def __init__(
        self,
        scene_name: str,
        scene_version: str,
        tdca_version: str = "v3.1.2",
        compiler: str = "TDCA-Dual-Protocol-Compiler-v1.0.0",
        output_dir: Optional[str] = None,
    ):
        self.scene_name = scene_name
        self.scene_version = scene_version
        self.tdca_version = tdca_version
        self.compiler = compiler
        self.output_dir = output_dir or "."
        self._seq = 0

    def generate(self, product: Optional[dict] = None) -> dict:
        """生成化合 NCA。"""
        product = product or {}
        self._seq += 1
        product_hash = hashlib.sha256(
            json.dumps(product, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        nca_id = f"TDCA-NCA-DUAL-{self.scene_name}-{self.scene_version}"
        timestamp = datetime.now(timezone.utc).isoformat()
        fc_id = f"TDCA-FC-{datetime.now().strftime('%Y%m%d')}-{self._seq:03d}-DUAL-{self.scene_name}"

        nca = {
            "NCA-ID": nca_id,
            "Function-Call-ID": fc_id,
            "Operation-Type": "CodeGen",
            "Operator": "Reasonix",
            "Timestamp": timestamp,
            "Scope": f"双协议化合产物存证（{self.scene_name} {self.scene_version}）",
            "Pre-State": {"Path": None, "Hash": None, "Size": 0},
            "Post-State": {
                "Path": f"dual-protocol/{self.scene_name}/",
                "Hash": f"sha256:{product_hash}",
                "Size": 0,
            },
            "Config-Right-Token": {
                "Scope": f"化合产物 {self.scene_name}",
                "Rollback": "回退至上一次通过版本",
                "Audit-Trail": "NCA 文件记录",
                "Human-Signature-Required": True,
                "Max-Retry": 0,
                "Granted-By": "TDCA-MEMO-006 + 场景制度委员会",
                "Expires": None,
            },
            "Audit-Trail": [
                {"Step": "操作执行: CodeGen", "Time": timestamp, "Evidence": f"sha256:{product_hash}"}
            ],
            "Human-Signature": {"Status": "Pending", "Signed-By": None, "Signed-At": None},
            "Negative-Space-Check": {"NSFL-Version": "V0.2", "Triggered": False, "Trigger-Reason": None},
            "MOU-Anchor": {
                "Status": "Simulated",
                "Total-Cost-CNY": None,
                "Tokens": None,
                "Cache-Ratio": None,
                "Inbound-Tax": None,
                "Outbound-Tax": None,
                "Note": "模拟态：真实税收锚定待 DCEP 接入（D-011）",
            },
            "Scene": {
                "name": self.scene_name,
                "version": self.scene_version,
                "tdca_version": self.tdca_version,
                "compiler": self.compiler,
            },
        }
        return nca

    def save(self, nca: dict, output_dir: Optional[str] = None) -> str:
        """保存 NCA 到 JSON 文件。"""
        out = Path(output_dir or self.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"dual-nca-{self.scene_name}.json"
        path.write_text(json.dumps(nca, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)


def main() -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="TDCA 双协议 NCA 生成器")
    parser.add_argument("--scene-name", required=True)
    parser.add_argument("--scene-version", default="v1.0.0")
    parser.add_argument("--output", default=".")
    args = parser.parse_args()

    gen = DualNcaGenerator(args.scene_name, args.scene_version)
    nca = gen.generate()
    path = gen.save(nca, args.output)
    print(f"✅ 双协议 NCA 生成完成: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
