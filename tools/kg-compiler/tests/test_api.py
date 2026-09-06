# SPDX-License-Identifier: Apache-2.0
"""TDCA-DEV-TASK-004 LIM-004 单元测试 — API Token 验证强化
Granted-By: TDCA-DEV-TASK-004
NSFL-Declaration: 测试验证 FC-002 委托验证逻辑（不依赖 FastAPI 安装）
"""
import os
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import _check_auth, _set_fc002_validator, TDCAHttpError, FASTAPI_AVAILABLE

# 双异常兼容（修复环境耦合——FastAPI 可用时 api.py 抛 HTTPException，否则 TDCAHttpError）
if FASTAPI_AVAILABLE:
    from fastapi import HTTPException
    HTTP_ERRORS = (TDCAHttpError, HTTPException)
else:
    HTTP_ERRORS = (TDCAHttpError,)


class TestLIM004TokenValidation(unittest.TestCase):
    def tearDown(self):
        _set_fc002_validator(None)

    def test_missing_token(self):
        """缺 Token → 401"""
        with self.assertRaises(HTTP_ERRORS) as ctx:
            _check_auth("")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_fc002_valid_token(self):
        """FC-002 验证通过"""
        validator = Mock()
        validator.validate_token.return_value = {'valid': True, 'expired': False, 'puf_bound': True}
        _set_fc002_validator(validator)
        _check_auth('TDCA-CRT-001')  # 不应抛异常
        validator.validate_token.assert_called_once_with('TDCA-CRT-001')

    def test_fc002_invalid_token(self):
        """FC-002 验证无效 → 401"""
        validator = Mock()
        validator.validate_token.return_value = {'valid': False, 'expired': False, 'puf_bound': True}
        _set_fc002_validator(validator)
        with self.assertRaises(HTTP_ERRORS) as ctx:
            _check_auth('TDCA-CRT-BAD')
        self.assertEqual(ctx.exception.status_code, 401)

    def test_fc002_expired_token(self):
        """Token 过期 → 401"""
        validator = Mock()
        validator.validate_token.return_value = {'valid': True, 'expired': True, 'puf_bound': True}
        _set_fc002_validator(validator)
        with self.assertRaises(HTTP_ERRORS) as ctx:
            _check_auth('TDCA-CRT-EXPIRED')
        self.assertEqual(ctx.exception.status_code, 401)

    def test_fc002_unbound_puf(self):
        """Token 未绑定 PUF → 401"""
        validator = Mock()
        validator.validate_token.return_value = {'valid': True, 'expired': False, 'puf_bound': False}
        _set_fc002_validator(validator)
        with self.assertRaises(HTTP_ERRORS) as ctx:
            _check_auth('TDCA-CRT-UNBOUND')
        self.assertEqual(ctx.exception.status_code, 401)

    def test_fc002_service_error(self):
        """FC-002 服务异常 → 503"""
        validator = Mock()
        validator.validate_token.side_effect = RuntimeError('down')
        _set_fc002_validator(validator)
        with self.assertRaises(HTTP_ERRORS) as ctx:
            _check_auth('TDCA-CRT-001')
        self.assertEqual(ctx.exception.status_code, 503)

    def test_development_prefix_check(self):
        """开发路径：前缀检查"""
        _check_auth('TDCA-CRT-001')  # 无 FC-002 注入 → 前缀通过
        with self.assertRaises(HTTP_ERRORS) as ctx:
            _check_auth('BAD-TOKEN')
        self.assertEqual(ctx.exception.status_code, 401)


if __name__ == '__main__':
    unittest.main()
