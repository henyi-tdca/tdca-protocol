# Security SLA（CI 第四条 · 严重级漏洞响应时限）

> 制度依据：`TDCA-SPEC-CI-SEC-SLA-001`（V1.0 · 2026-10-22 生效）｜ 工程落地：`.github/workflows/security-sla.yml` ｜ 本页一页说明，口径以制度件为准。

## 一、严重级界定

- 触发标签：issue 打 `security-critical` 即入严重级（含 CVSS 严重级、已观察在野利用之 CVE，如 `PHP2Shell`／`CVE-2026-109618` 类）。
- 打标即知悉：无人工输入时，`know_time` 缺省取打标签事件时间。

## 二、三段时限（皆自 `know_time` 起算）

| 阶段 | 时限 | 在 workflow 输出 |
|---|---|---|
| 排查 | ≤ 2 小时 | `recon` |
| 处置 | ≤ 24 小时 | `remedy` |
| 复盘 | ≤ 48 小时 | `review` |

判定值三态：`PASS`（时限内）／`LATE`（超时）／`MISSING`（无证据）。

## 三、证据口径（可指认件）

- **issue 评论时间戳**：阶段完成以该阶段首个标记评论为准——`【排查回报】`、`【处置完成】`／`【处置】`、`【复盘】`。
- **仓内可指认件**：回报件文件名＋`sha256_16`，由人工贴入对应阶段评论作为证据体；判定取评论时间戳，不解析件内时间自报值。

## 四、例外与责任

- **例外仅创始人**：时限豁免、降级、销项须创始人明示并在 issue 留痕；其余任何侧无权宽限。
- 责任分侧：智库出制度与裁定；执行侧跑门与回报；走查侧核证；创始人握例外与最终裁决。

## 五、工程约束（本工作流自述）

- **只新增**：本 workflow 为事件门，⛔ 不进 `push`／`pull_request` 触发链，⛔ 与三律日常门禁抢路，不阻断日常构建。
- **触发两条**：`workflow_dispatch`（`know_time` 必填、`issue_number` 可空）＋ `issues` 打 `security-critical` 标签。
- **零凭据零新依赖**：只读仓内文件与 issue 元数据（`contents: read`／`issues: read`），不写件、不改 issue、不联网抓取。

## 六、用法示例

```bash
# 人工判定某安全事件 issue：
gh workflow run security-sla.yml -f issue_number=123 -f know_time=2026-10-22T02:00:00+08:00
# 结果见 run 的 Job summary 与输出 recon/remedy/review 三值。
```
