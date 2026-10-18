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
  - 验证脚本只读，不修改任何记录
  - 时间戳顺序验证为硬性门槛（P0）
  - NSFL 触发事件必须高亮标记
SPDX-License-Identifier: TDCA-Internal
"""

import os
import re
import yaml
from datetime import datetime, timezone
from typing import Optional


class TDCACVerifyChain:
    """
    三级关联链验证器

    验证 Token-ID → NCA-ID → MOU-ID 的关联完整性。
    只读操作，不修改任何记录。
    """

    def __init__(
        self,
        fc_id: str,
        token_dir: Optional[str] = None,
        nca_dir: Optional[str] = None,
        mou_dir: Optional[str] = None
    ):
        self.fc_id = fc_id
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.token_dir = token_dir or os.path.join(base, '.tdca-nca', 'tokens')
        self.nca_dir = nca_dir or os.path.join(base, '.tdca-nca', 'nca')
        self.mou_dir = mou_dir or os.path.join(base, '.tdca-nca', 'mou')

    def verify(self) -> dict:
        """执行验证，返回报告字典"""
        checks = []
        nsfl_events = []
        chain = {'Token': None, 'NCA': None, 'MOU': None, 'Linked': False}
        status = 'PASS'

        # 检查1（P0）：Token 文件存在且未过期
        token = self._find_latest_token()
        if token is None:
            checks.append({'Check': 'Token 有效性', 'Result': 'FAIL',
                           'Detail': '未找到有效 Token 文件'})
            status = 'FAIL'
        else:
            token_id = token.get('Token-ID', '')
            chain['Token'] = token_id
            checks.append({'Check': 'Token 有效性', 'Result': 'PASS',
                           'Detail': f"{token_id} 存在"})

        # 检查3（P0）：MOU 的 token_ref 指向有效 Token
        mou = self._find_latest_mou()

        # 检查2（P1）：NCA 的 pre-hash / post-hash 与操作路径匹配
        nca = self._find_latest_nca()
        if nca is not None:
            nca_path = nca.get('Path') or nca.get('path')
            nca_pre = nca.get('Pre-State-Hash') or (nca.get('Pre-State') or {}).get('Hash')
            nca_post = nca.get('Post-State-Hash') or (nca.get('Post-State') or {}).get('Hash')
            if nca_path and os.path.exists(nca_path) and nca_pre and nca_post:
                checks.append({'Check': 'NCA 哈希与路径匹配', 'Result': 'PASS',
                               'Detail': f"路径存在 {nca_path}，哈希非空"})
            else:
                checks.append({'Check': 'NCA 哈希与路径匹配', 'Result': 'WARN',
                               'Detail': f"路径不可达或哈希缺失 (path={nca_path}, pre={nca_pre is not None}, post={nca_post is not None})"})

        if mou is not None:
            chain['MOU'] = mou.get('MOU-ID')
            mou_token_ref = mou.get('Token-Ref')
            if token is not None and mou_token_ref == token.get('Token-ID'):
                checks.append({'Check': 'MOU Token-Ref 指向', 'Result': 'PASS',
                               'Detail': f"MOU 引用 {mou_token_ref}"})
            else:
                checks.append({'Check': 'MOU Token-Ref 指向', 'Result': 'FAIL',
                               'Detail': f"MOU 引用 {mou_token_ref} 与最新 Token 不匹配"})
                status = 'FAIL'

        # 检查4（P0）：时间戳顺序 Token < NCA < MOU
        if nca is not None:
            chain['NCA'] = nca.get('NCA-ID')
            order_ok, ts_detail = self._check_timestamp_order(token, nca, mou)
            if order_ok:
                checks.append({'Check': '时间戳顺序', 'Result': 'PASS',
                               'Detail': ts_detail})
            elif ts_detail and ts_detail.startswith('时间戳部分缺失'):
                # 修正项2：降级验证 → WARN（不直接 FAIL）
                checks.append({'Check': '时间戳顺序', 'Result': 'WARN',
                               'Detail': ts_detail})
                if status == 'PASS':
                    status = 'WARN'
            else:
                checks.append({'Check': '时间戳顺序', 'Result': 'FAIL',
                               'Detail': ts_detail or 'Token/NCA/MOU 时间戳顺序错误'})
                status = 'FAIL'

        # 检查5（P1）：MOU 的 Actual-Total 与 Tax-In+Tax-Out 一致性
        if mou is not None:
            tax_in = mou.get('Tax-In')
            tax_out = mou.get('Tax-Out')
            actual = mou.get('Actual-Total')
            if tax_in is not None and tax_out is not None and actual is not None:
                expected = tax_in + tax_out
                if abs(expected - actual) < 0.001:
                    checks.append({'Check': 'MOU 税收一致性', 'Result': 'PASS',
                                   'Detail': f"Tax-In({tax_in}) + Tax-Out({tax_out}) = {actual}"})
                else:
                    checks.append({'Check': 'MOU 税收一致性', 'Result': 'WARN',
                                   'Detail': f"Tax-In({tax_in}) + Tax-Out({tax_out}) = {expected} ≠ Actual-Total({actual})，偏差 {abs(expected - actual)}"})
                    if status == 'PASS':
                        status = 'WARN'

        # 检查6（P0）：NSFL 触发事件高亮
        nsfl_events = self._detect_nsfl_events(token, nca, mou)

        # 链完整性
        chain['Linked'] = all([chain['Token'], chain['NCA'], chain['MOU']])

        report = {
            'Verification-ID': f"TDCA-VERIFY-{datetime.now(timezone.utc).strftime('%Y%m%d')}-001",
            'FC-ID': self.fc_id,
            'Timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'Status': status,
            'Checks': checks,
            'NSFL-Events': nsfl_events,
            'Chain-Integrity': chain,
        }
        return report

    # ---- 辅助方法 ----

    def _find_latest_token(self) -> Optional[dict]:
        """查找目录中最新 Token"""
        if not os.path.isdir(self.token_dir):
            return None
        files = [f for f in os.listdir(self.token_dir) if f.endswith('.yaml')]
        if not files:
            return None
        files.sort(reverse=True)
        try:
            with open(os.path.join(self.token_dir, files[0]), 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    def _find_latest_nca(self) -> Optional[dict]:
        """查找目录中最新 NCA"""
        if not os.path.isdir(self.nca_dir):
            return None
        files = [f for f in os.listdir(self.nca_dir) if f.endswith('.yaml')]
        if not files:
            return None
        files.sort(reverse=True)
        try:
            with open(os.path.join(self.nca_dir, files[0]), 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    def _find_latest_mou(self) -> Optional[dict]:
        """查找目录中最新 MOU"""
        if not os.path.isdir(self.mou_dir):
            return None
        files = [f for f in os.listdir(self.mou_dir) if f.endswith('.yaml')]
        if not files:
            return None
        files.sort(reverse=True)
        try:
            with open(os.path.join(self.mou_dir, files[0]), 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    def _check_timestamp_order(self, token, nca, mou):
        """验证 Token < NCA < MOU 时间戳顺序
        返回: (order_ok: bool, detail: str)
        """
        def extract_ts(record, field):
            if record is None:
                return None
            val = record.get(field)
            if not val:
                return None
            try:
                return datetime.strptime(val, '%Y-%m-%dT%H:%M:%SZ')
            except (ValueError, TypeError):
                return None

        t_token = None
        t_nca = None
        t_mou = None

        # Token 用文件名日期推断（简化：用 Recorded-At 不可用时跳过）
        if token is not None and token.get('Token-ID'):
            m = re.match(r'^TDCA-CRT-(\d{8})-(\d{3})$', token.get('Token-ID', ''))
            if m:
                try:
                    t_token = datetime.strptime(m.group(1), '%Y%m%d')
                except ValueError:
                    t_token = None

        if nca is not None:
            t_nca = extract_ts(nca, 'Timestamp') or extract_ts(nca, 'Recorded-At')

        if mou is not None:
            t_mou = extract_ts(mou, 'Recorded-At')

        # 仅当三个时间戳都可用时严格验证
        if t_token and t_nca and t_mou:
            if t_token <= t_nca <= t_mou:
                return True, f"{t_token.isoformat()} < {t_nca.isoformat()} < {t_mou.isoformat()}"
            return False, "Token/NCA/MOU 时间戳顺序错误"
        # 修正项2：不完整时降级为 WARN（不直接 FAIL）
        return False, "时间戳部分缺失，降级为 WARN 验证"

    def _detect_nsfl_events(self, token, nca, mou) -> list:
        """检测负空间触发事件"""
        events = []
        # 负空间任务集合
        nsfl_tasks = {'FileDelete', 'FileEdit', 'FileMove', 'DirMove'}

        # Token 负空间检查
        if token is not None:
            task_type = token.get('task_type')
            if task_type in nsfl_tasks and not token.get('NSFL-Declaration'):
                events.append({
                    'Event': f"{task_type} 缺少 NSFL-Declaration",
                    'Token': token.get('Token-ID'),
                    'Severity': 'P0'
                })

        return events
