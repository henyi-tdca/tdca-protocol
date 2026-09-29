"""TDCA-FC-20260801-003 任务B 补充测试 — 子命令分发
Granted-By: TDCA-MEMO-008
NSFL-Declaration: 测试调用子命令函数，验证模块衔接，不伪造税收数据
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 工作空间根目录（包含已归档的 tdca_nca_generator 与 tdca_config_right_token_generator）
_ws_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..')
if os.path.isfile(os.path.join(_ws_root, 'tdca_nca_generator.py')):
    sys.path.insert(0, os.path.abspath(_ws_root))
else:
    # 备选：已归档到 .tdca-nca/scripts/
    sys.path.insert(0, os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        '.tdca-nca', 'scripts')))

import tdca_tool
from tdca_tool import cmd_token, cmd_nca, cmd_mou, build_parser


def make_args(subcommand, *sub_options, token=None, risk='LOW'):
    argv = []
    if token:
        argv += ['--token', token]
    if risk != 'LOW':
        argv += ['--risk', risk]
    argv += [subcommand] + list(sub_options)
    return build_parser().parse_args(argv)


class TestSubcommands(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.tokens = os.path.join(self.tmp, 'tokens')
        self.mous = os.path.join(self.tmp, 'mou')

    def test_cmd_token_calls_generator(self):
        """token 子命令调用 TDCAConfigRightTokenGenerator"""
        args = make_args('token', '--type', 'Review', '--path', os.path.join(self.tmp, 'x'),
                         token='TDCA-CRT-001')
        with patch('tdca_config_right_token_generator.TDCAConfigRightTokenGenerator') as MockGen:
            instance = MockGen.return_value
            instance.generate.return_value = {'Token-ID': 'TDCA-CRT-20260801-999'}
            instance.to_yaml.return_value = 'Token-ID: TDCA-CRT-20260801-999'
            instance.save.return_value = 'saved.yaml'
            cmd_token(args)
            MockGen.assert_called_once()

    def test_cmd_nca_calls_generator(self):
        """nca 子命令调用 TDCANCAGenerator"""
        args = make_args('nca', '--type', 'CodeGen', '--path', os.path.join(self.tmp, 'x.py'),
                         '--pre-hash', 'a' * 64, '--post-hash', 'b' * 64, token='TDCA-CRT-001')
        with patch('tdca_nca_generator.TDCANCAGenerator') as MockGen:
            instance = MockGen.return_value
            instance.generate.return_value = 'nca.yaml'
            cmd_nca(args)
            MockGen.assert_called_once()

    def test_cmd_mou_calls_recorder(self):
        """mou 子命令调用 TDCAMOURecorder"""
        args = make_args('mou', '--token-ref', 'TDCA-CRT-20260801-001',
                         '--pre-est', '1000.0', token='TDCA-CRT-001')
        with patch('tdca_mou_recorder.TDCAMOURecorder') as MockRec:
            instance = MockRec.return_value
            instance.record.return_value = {
                'MOU-ID': 'TDCA-MOU-20260801-001',
                'Token-Ref': 'TDCA-CRT-20260801-001',
                'Tax-In': None, 'Tax-Out': None, 'Actual-Total': None,
                'Pre-Est': 1000.0, 'Pre-Est-Status': '[SIMULATED]',
                'Activation-Coefficient': None,
                'Recorded-At': '2026-08-01T10:00:00Z',
            }
            instance.to_yaml.return_value = 'MOU-ID: TDCA-MOU-20260801-001'
            instance.save.return_value = 'mou.yaml'
            cmd_mou(args)
            MockRec.assert_called_once()

    def test_cmd_mou_with_gov_pcr(self):
        """mou 子命令 + gov_pcr 计算激活系数"""
        args = make_args('mou', '--token-ref', 'TDCA-CRT-20260801-001',
                         '--tax-in', '500', '--tax-out', '300', '--gov-pcr', '400',
                         token='TDCA-CRT-001')
        with patch('tdca_mou_recorder.TDCAMOURecorder') as MockRec:
            instance = MockRec.return_value
            instance.record.return_value = {
                'MOU-ID': 'TDCA-MOU-20260801-001',
                'Token-Ref': 'TDCA-CRT-20260801-001',
                'Tax-In': 500.0, 'Tax-Out': 300.0, 'Actual-Total': 800.0,
                'Pre-Est': None, 'Pre-Est-Status': None,
                'Activation-Coefficient': None,
                'Recorded-At': '2026-08-01T10:00:00Z',
            }
            instance.compute_activation_coefficient.return_value = 2.0
            instance.to_yaml.return_value = 'ok'
            instance.save.return_value = 'mou.yaml'
            cmd_mou(args)
            instance.compute_activation_coefficient.assert_called_once()


if __name__ == '__main__':
    unittest.main()
