"""TDCA-FC-20260801-003 任务B 单元测试 — tdca-tool CLI
Granted-By: TDCA-MEMO-008
NSFL-Declaration: 测试仅验证权限自洽逻辑，不触发真实业务副作用
"""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tdca_tool import _check_auth, build_parser


def make_args(subcommand, *sub_options, token=None, risk='LOW', signature=None):
    """构造正确的参数序列：全局选项在前，子命令+子选项在后"""
    argv = []
    if token:
        argv += ['--token', token]
    if risk != 'LOW':
        argv += ['--risk', risk]
    if signature:
        argv += ['--signature', signature]
    argv += [subcommand] + list(sub_options)
    return build_parser().parse_args(argv)


class TestCLIAuth(unittest.TestCase):
    def test_nsfl_trigger_missing_token(self):
        """NSFL-TRIGGER：缺少 TDCA_TOKEN"""
        args = make_args('token', '--type', 'FileMove', '--path', '/tmp')
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(PermissionError) as ctx:
                _check_auth(args)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_nsfl_trigger_high_risk_no_signature(self):
        """NSFL-TRIGGER：HIGH 风险但无签名"""
        args = make_args('token', '--type', 'FileEdit', '--path', '/tmp',
                         token='TDCA-CRT-001', risk='HIGH')
        with self.assertRaises(PermissionError) as ctx:
            _check_auth(args)
        self.assertIn('[NSFL-TRIGGER]', str(ctx.exception))

    def test_low_risk_no_signature_allowed(self):
        """LOW 风险无需签名"""
        args = make_args('token', '--type', 'Review', '--path', '/tmp', token='TDCA-CRT-001')
        _check_auth(args)  # 不应抛异常

    def test_high_risk_with_signature_allowed(self):
        """HIGH 风险 + 签名通过"""
        args = make_args('token', '--type', 'FileEdit', '--path', '/tmp',
                         token='TDCA-CRT-001', risk='HIGH', signature='HUMAN-SIG')
        _check_auth(args)  # 不应抛异常

    def test_env_token_used(self):
        """环境变量 TDCA_TOKEN 可用"""
        args = make_args('token', '--type', 'Review', '--path', '/tmp')
        with patch.dict(os.environ, {'TDCA_TOKEN': 'ENV-TOKEN'}, clear=True):
            _check_auth(args)  # 不应抛异常

    def test_version_flag(self):
        """--version 输出（SystemExit 0）"""
        import argparse
        with self.assertRaises(SystemExit) as ctx:
            build_parser().parse_args(['--version'])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == '__main__':
    unittest.main()
