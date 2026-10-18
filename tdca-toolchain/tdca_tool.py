"""
TDCA-FC-20260801-003 修正声明:
  - P0: 模块命名由 TDCAMOUGenerator 修正为 TDCAMOURecorder
  - P0: 核心方法由 generate() 修正为 record()
  - P0: Pre-Est 字段强制标记 [SIMULATED]
  - P0: Activation-Coefficient 禁止基于 Pre-Est 计算
  - P1: tdca-tool CLI 增加权限自洽检查 _check_auth()
  - P1: HIGH 风险操作强制人类签名

制度锚定: TDCA-PRINCIPLE-MOU-001, ID79, TDCA-MEMO-008
Granted-By: TDCA-MEMO-008

NSFL-Declaration:
  - CLI 权限检查遵循"就高不就低"原则
  - HIGH 风险操作未签名即拒绝执行
  - 子命令各自调用对应模块，不内联业务逻辑
SPDX-License-Identifier: TDCA-Internal
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timezone

# 版本
TOOLCHAIN_VERSION = "1.0.0"

# 审计日志
CLI_AUDIT_LOG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    '.tdca-nca', 'cli-audit.log'
)


def _check_auth(args) -> None:
    """
    配置权调用前置检查：
      1. 检查 TDCA_TOKEN 环境变量或 --token 参数
      2. 若 --risk HIGH 且未提供 --signature，拒绝执行
      3. 记录操作日志到 .tdca-nca/cli-audit.log
    """
    token = os.environ.get('TDCA_TOKEN') or getattr(args, 'token', None)
    if not token:
        raise PermissionError("[NSFL-TRIGGER] 缺少 TDCA_TOKEN，配置权调用需身份锚定")

    if getattr(args, 'risk', 'LOW') == 'HIGH' and not getattr(args, 'signature', None):
        raise PermissionError("[NSFL-TRIGGER] HIGH 风险操作需人类签名 --signature")

    _log_audit(args, status='SUCCESS')


def _log_audit(args, status: str):
    """写入 CLI 审计日志"""
    try:
        os.makedirs(os.path.dirname(CLI_AUDIT_LOG), exist_ok=True)
        ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        subcommand = getattr(args, 'subcommand', 'unknown')
        key_params = ' '.join(f"{k}={v}" for k, v in vars(args).items()
                              if v is not None and k not in ('func', 'subcommand'))
        line = f"{ts} | tdca-tool {subcommand} | {key_params} | token={getattr(args, 'token', 'N/A')} | status={status}\n"
        with open(CLI_AUDIT_LOG, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass  # 审计日志写入失败不阻断主流程


# ---- 子命令实现（各自调用对应模块，不内联逻辑）----

def cmd_token(args):
    """配置权前置声明：调用 TDCAConfigRightTokenGenerator"""
    from tdca_config_right_token_generator import TDCAConfigRightTokenGenerator
    gen = TDCAConfigRightTokenGenerator(
        task_type=args.type,
        target_path=args.path,
        operator=args.operator,
        risk_level=args.risk,
        description=args.description
    )
    token = gen.generate()
    print(gen.to_yaml(token))
    # 保存
    saved = gen.save(token)
    print(f"\n[OK] Token 已保存: {saved}")


def cmd_nca(args):
    """嵌套认知资产记录：调用 TDCANCAGenerator"""
    from tdca_nca_generator import TDCANCAGenerator
    gen = TDCANCAGenerator(
        operation_type=args.type,
        path=args.path,
        pre_state_hash=args.pre_hash,
        post_state_hash=args.post_hash,
        operator=args.operator
    )
    path = gen.generate()
    print(f"[OK] NCA 已生成: {path}")


def cmd_mou(args):
    """MOU 计量锚定：调用 TDCAMOURecorder"""
    from tdca_mou_recorder import TDCAMOURecorder
    recorder = TDCAMOURecorder(
        token_ref=args.token_ref,
        nca_ref=args.nca_ref,
        pre_est=args.pre_est,
        operator=args.operator
    )
    record = recorder.record(tax_in=args.tax_in, tax_out=args.tax_out)

    # 若提供 gov_pcr 且 Actual-Total 非空，计算激活系数
    if args.gov_pcr is not None and record.get('Actual-Total') is not None:
        coeff = recorder.compute_activation_coefficient(
            actual_total=record['Actual-Total'],
            gov_pcr=args.gov_pcr,
            employment_ss=args.employment_ss or 0
        )
        record['Activation-Coefficient'] = coeff
        recorder.validate(record)  # 更新后重新自证

    print(recorder.to_yaml(record))
    saved = recorder.save(record)
    print(f"\n[OK] MOU 已保存: {saved}")


def cmd_verify(args):
    """三级关联链验证：调用 tdca_verify_chain"""
    from tdca_verify_chain import TDCACVerifyChain
    verifier = TDCACVerifyChain(
        fc_id=args.fc_id,
        token_dir=args.token_dir,
        nca_dir=args.nca_dir,
        mou_dir=args.mou_dir
    )
    report = verifier.verify()
    import yaml
    report_yaml = yaml.dump(report, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
    print(report_yaml)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report_yaml)
        print(f"\n[OK] 验证报告已保存: {args.output}")


def build_parser():
    parser = argparse.ArgumentParser(prog='tdca-tool', description='TDCA 工具链统一入口')
    parser.add_argument('--version', action='version', version=f'TDCA-Toolchain v{TOOLCHAIN_VERSION}')
    parser.add_argument('--token', help='配置权 Token（或设置环境变量 TDCA_TOKEN）')
    parser.add_argument('--risk', choices=['LOW', 'MEDIUM', 'HIGH'], default='LOW', help='风险等级')
    parser.add_argument('--signature', help='人类签名（HIGH 风险必填）')

    sub = parser.add_subparsers(dest='subcommand', required=True)

    # token 子命令
    p_token = sub.add_parser('token', help='配置权前置声明')
    p_token.add_argument('--type', required=True, help='任务类型')
    p_token.add_argument('--path', required=True, help='目标路径')
    p_token.add_argument('--operator', default='Reasonix')
    p_token.add_argument('--description', default=None)
    p_token.set_defaults(func=cmd_token)

    # nca 子命令
    p_nca = sub.add_parser('nca', help='嵌套认知资产记录')
    p_nca.add_argument('--type', required=True, help='操作类型')
    p_nca.add_argument('--path', required=True, help='目标路径')
    p_nca.add_argument('--pre-hash', dest='pre_hash', required=True, help='操作前哈希')
    p_nca.add_argument('--post-hash', dest='post_hash', required=True, help='操作后哈希')
    p_nca.add_argument('--operator', default='Reasonix')
    p_nca.set_defaults(func=cmd_nca)

    # mou 子命令
    p_mou = sub.add_parser('mou', help='MOU 计量锚定')
    p_mou.add_argument('--token-ref', dest='token_ref', required=True, help='Config-Right-Token ID')
    p_mou.add_argument('--nca-ref', dest='nca_ref', default=None)
    p_mou.add_argument('--pre-est', dest='pre_est', type=float, default=None, help='预估值（标记 [SIMULATED]）')
    p_mou.add_argument('--tax-in', dest='tax_in', type=float, default=None, help='进项税收')
    p_mou.add_argument('--tax-out', dest='tax_out', type=float, default=None, help='出项税收')
    p_mou.add_argument('--gov-pcr', dest='gov_pcr', type=float, default=None, help='政府初始PCR投入')
    p_mou.add_argument('--employment-ss', dest='employment_ss', type=float, default=None, help='就业社保')
    p_mou.add_argument('--operator', default='Reasonix')
    p_mou.set_defaults(func=cmd_mou)

    # verify 子命令
    p_verify = sub.add_parser('verify', help='三级关联链验证')
    p_verify.add_argument('--fc-id', dest='fc_id', required=True, help='Function-Call-ID')
    p_verify.add_argument('--token-dir', dest='token_dir', default=None)
    p_verify.add_argument('--nca-dir', dest='nca_dir', default=None)
    p_verify.add_argument('--mou-dir', dest='mou_dir', default=None)
    p_verify.add_argument('--output', default=None, help='验证报告输出路径')
    p_verify.set_defaults(func=cmd_verify)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # 权限自洽检查（每次调用前执行）
    _check_auth(args)

    # 分发到对应模块
    args.func(args)


if __name__ == '__main__':
    main()
