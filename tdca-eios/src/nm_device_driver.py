"""NMDeviceDriver — 通知机设备驱动抽象层（M4，E-HW-1 兼容）

制度锚定: E-HW-1 六层架构硬件映射 + CBDC 唯一性 + MOU 锚定
当前为 mock 实现；E-HW-2 硬件制造到位后替换为真实驱动（A7100 SE / SRAM PUF）。
模拟态: 通知机硬件未投产部署，本驱动为 mock 模拟（SIL），不构成真实部署。
NSFL: 接口签名不得偏离 TDCA-PHASE-E-HW-1 硬件规格书。
"""

import hashlib


class NMDeviceDriver:
    """通知机设备驱动抽象层（E-HW-1 规格书兼容）

    当前为 mock 实现，E-HW-2 硬件到位后替换为真实驱动。
    """

    def __init__(self, batch_id: str = "B20260804"):
        self.batch_id = batch_id
        self._mock_puf = "SRAM-PUF-MOCK-{}-A1B2C3D4".format(batch_id)

    # ---- E-HW-1 规格书接口：PUF / TDID / 熔断 / OTA / L1 登记 ----

    def read_puf(self) -> str:
        """读取 PUF 物理不可克隆函数指纹

        硬件实现: SRAM PUF（长光华芯降维方案）
        当前 mock: 返回模拟指纹
        """
        return self._mock_puf

    def generate_td_id(self, puf_fingerprint: str, constitution_hash: str, batch_id: str) -> str:
        """生成 TDID（TDCA Device ID）

        公式: TDID = SHA256(PUF指纹 || 宪法哈希 || 批次号)
        硬件实现: A7100 SE 安全芯片注入（不可导出）
        """
        raw = (puf_fingerprint + "||" + constitution_hash + "||" + batch_id).encode("utf-8")
        return "TDID-" + hashlib.sha256(raw).hexdigest()[:32].upper()

    def trigger_physical_fuse(self, reason: str, level: str) -> bool:
        """触发物理熔断器（法律禁止操作硬件阻断）

        硬件实现: 六层架构 L0 熔断电路（微动开关+光敏+温度）
        当前 mock: 记录日志，返回 True
        level: LEVEL_1/2/3（NSFL 分级熔断）
        """
        if level not in ("LEVEL_1", "LEVEL_2", "LEVEL_3"):
            raise ValueError("[NSFL-TRIGGER] 非法熔断级别: %s" % level)
        # mock: 记录日志
        print("[NM-FUSE] reason=%s level=%s -> FUSED(mock)" % (reason, level))
        return True

    def ota_update(self, firmware_hash: str, constitution_ota: dict) -> bool:
        """OTA 升级（固件 + 宪法活宪法同步）

        硬件实现: 安全芯片 OTA 接口（验证哈希后写入）
        当前 mock: 验证哈希，返回 True
        """
        if not firmware_hash.startswith("sha256:"):
            raise ValueError("[NSFL-TRIGGER] 固件哈希格式非法: %s" % firmware_hash)
        version = constitution_ota.get("version", "TDCA-CONST-unknown")
        print("[NM-OTA] firmware=%s constitution=%s -> OK(mock)" % (firmware_hash[:20], version))
        return True

    def register_to_l1(self, tdid: str, ownership_record: dict) -> dict:
        """通知机首次激活：L1 所有权登记

        触发: "安装即同意协议"硬件签名 → FC-002 权限分配 → TIMA L1 记录
        """
        required = {"owner_did", "config_right_hash"}
        missing = required - set(ownership_record.keys())
        if missing:
            raise ValueError("[NSFL-TRIGGER] 所有权记录缺少字段: %s" % sorted(missing))
        return {
            "tdid": tdid,
            "l1_record": ownership_record,
            "registered": True,
            "nca_ref": "NCA-TDID-" + tdid[5:15],
        }


if __name__ == "__main__":  # pragma: no cover（演示块，非交付逻辑）
    drv = NMDeviceDriver()
    puf = drv.read_puf()
    td = drv.generate_td_id(puf, "sha256:9beb123c50b5cf18775b5cfd5c2cf8fd08b224261119becbfe913e0e03b6d601", "B20260804")
    print("PUF:", puf)
    print("TDID:", td)
    drv.trigger_physical_fuse("法律禁止操作", "LEVEL_3")
    drv.ota_update("sha256:abcd", {"version": "TDCA-CONST-v3.1.2"})
    print(drv.register_to_l1(td, {"owner_did": "did:tdca:创始人", "config_right_hash": "cfg-001"}))
