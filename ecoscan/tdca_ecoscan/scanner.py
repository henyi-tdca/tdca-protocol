"""tdca_ecoscan · 雷达扫描（DCD-ECOSCAN-001 M1 scanner）

GitHub API 关键词扫描 + 活跃过滤 + 增量更新。
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import quote


@dataclass(frozen=True)
class ScanTarget:
    """扫描候选仓库。"""
    repo_full: str              # owner/repo
    stars: int
    license_spdx: Optional[str]
    pushed_at: Optional[str]
    description: Optional[str]
    keywords: List[str]
    url: str

    def to_dict(self) -> dict:
        return {
            "repo_full": self.repo_full,
            "stars": self.stars,
            "license_spdx": self.license_spdx,
            "pushed_at": self.pushed_at,
            "description": self.description,
            "keywords": self.keywords,
            "url": self.url,
        }


class EcoScanner:
    """生态雷达扫描器（M1）。"""

    # 扫描关键词（DCD-ECOSCAN-001 §二）
    DEFAULT_KEYWORDS = [
        "agent framework", "mcp server", "agent protocol", "agent orchestration",
        "ai governance", "agent governance", "plugin system", "harness",
    ]

    def __init__(self, keywords: Optional[List[str]] = None,
                 min_stars: int = 100,
                 max_results_per_query: int = 20):
        self._keywords = keywords or list(self.DEFAULT_KEYWORDS)
        self._min_stars = min_stars
        self._max_results = max_results_per_query

    # ---- GitHub API 扫描（真实执行）----

    def scan_github(self, token: Optional[str] = None,
                    max_queries: int = 3) -> List[ScanTarget]:
        """真实 GitHub API 扫描（Search API，无 token 限速）。

        返回: ScanTarget 列表（License 合规前置 AUDIT-001——仅保留有 SPDX 的公开仓）。
        """
        import urllib.request

        targets: List[ScanTarget] = []
        seen = set()
        for kw in self._keywords[:max_queries]:
            q = quote(f"{kw} in:name,description,readme stars:>{self._min_stars} license:mit,apache-2.0")
            url = f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page={self._max_results}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "tdca-ecoscan",
                "Accept": "application/vnd.github+json",
            })
            if token:
                req.add_header("Authorization", f"Bearer {token}")
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode())
            except Exception:
                continue  # 单查询失败不中断
            for item in data.get("items", []):
                full = item.get("full_name", "")
                lic = (item.get("license") or {}).get("spdx_id")
                if full in seen or not lic:
                    continue
                seen.add(full)
                targets.append(ScanTarget(
                    repo_full=full,
                    stars=item.get("stargazers_count", 0),
                    license_spdx=lic,
                    pushed_at=item.get("pushed_at"),
                    description=(item.get("description") or "")[:200],
                    keywords=[kw],
                    url=item.get("html_url", f"https://github.com/{full}"),
                ))
            time.sleep(0.5)  # 限速礼貌
        return targets

    # ---- 离线/测试模式（数据注入，ID92 SIMULATED）----

    # OSI 许可白名单（AUDIT-001 仓库优先——仅接受公开 OSI 许可）
    OSI_LICENSES = {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause",
                    "MPL-2.0", "GPL-3.0", "GPL-2.0", "LGPL-3.0", "AGPL-3.0"}

    def scan_static(self, repos: List[dict]) -> List[ScanTarget]:
        """静态注入扫描（测试/离线用——数据性质 SIMULATED）。"""
        targets = []
        for r in repos:
            lic = r.get("license_spdx")
            if not lic or lic not in self.OSI_LICENSES:
                raise ValueError(
                    f"[NSFL-TRIGGER] 非 OSI 许可（AUDIT-001 拒绝）: {r.get('repo_full')} -> {lic}")
            targets.append(ScanTarget(
                repo_full=r["repo_full"],
                stars=r.get("stars", 0),
                license_spdx=lic,
                pushed_at=r.get("pushed_at"),
                description=r.get("description"),
                keywords=r.get("keywords", []),
                url=r.get("url", f"https://github.com/{r['repo_full']}"),
            ))
        return targets

    def is_recent(self, target: ScanTarget, days: int = 30) -> bool:
        """活跃过滤（pushed_at 在 N 天内）。"""
        if not target.pushed_at:
            return False
        try:
            pushed = datetime.fromisoformat(target.pushed_at.replace("Z", "+00:00"))
        except ValueError:
            return False
        now = datetime.now(timezone.utc)
        return (now - pushed).days <= days
