# -*- coding: utf-8 -*-
"""Phase 4: 硬件接口仿真冒烟（5 用例）
覆盖: NMDeviceDriver 专项（E-HW-1 规格书一致性）
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPhase4HW(unittest.TestCase):
    """SMOKE-4-01 ~ 4-05: 硬件接口仿真（E-HW-1 规格书）"""

    def test_01_puf_fingerprint_unique(self):
        """SMOKE-4-01: PUF 指纹设备唯一性（不同批次不同指纹）"""
        from nm_device_driver import NMDeviceDriver
        p1 = NMDeviceDriver(batch_id='BATCH-A').read_puf()
        p2 = NMDeviceDriver(batch_id='BATCH-B').read_puf()
        self.assertNotEqual(p1, p2)
        self.assertIn('BATCH-A', p1)

    def test_02_tdid_formula(self):
        """SMOKE-4-02: TDID 公式（SHA256(PUF‖宪法哈希‖批次号)）可重现"""
        import hashlib
        from nm_device_driver import NMDeviceDriver
        drv = NMDeviceDriver()
        puf, ch, batch = 'fp-xyz', 'sha256:abcdef', 'B-01'
        expected = 'TDID-' + hashlib.sha256(
            ('fp-xyz||sha256:abcdef||B-01').encode()).hexdigest()[:32].upper()
        self.assertEqual(drv.generate_td_id(puf, ch, batch), expected)

    def test_03_fuse_invalid_level_nsfl(self):
        """SMOKE-4-03: 非法熔断级别触发 NSFL"""
        from nm_device_driver import NMDeviceDriver
        drv = NMDeviceDriver()
        with self.assertRaises(ValueError) as ctx:
            drv.trigger_physical_fuse('x', 'LEVEL_9')
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_04_ota_firmware_hash_validation(self):
        """SMOKE-4-04: OTA 固件哈希格式校验（非 sha256: 拒绝）"""
        from nm_device_driver import NMDeviceDriver
        drv = NMDeviceDriver()
        with self.assertRaises(ValueError) as ctx:
            drv.ota_update('deadbeef', {'version': 'TDCA-CONST-v3.1.2'})
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_05_l1_register_missing_field_nsfl(self):
        """SMOKE-4-05: L1 登记缺字段触发 NSFL"""
        from nm_device_driver import NMDeviceDriver
        drv = NMDeviceDriver()
        with self.assertRaises(ValueError) as ctx:
            drv.register_to_l1('TDID-X', {'owner_did': 'did:tdca:甲'})  # 缺 config_right_hash
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
