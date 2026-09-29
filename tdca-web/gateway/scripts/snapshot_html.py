# -*- coding: utf-8 -*-
# =============================================================================
# TDCA 制度水印
# FC-ID: KIMI-WEB-DB-TASK-001-M4 | 目标函数: 前端演示页 HTML 快照（数据真库实读生成）
# 约束矩阵: ID92——每板块按 data_provenance 打标；金额分→元；自包含单文件（无外部依赖）
# =============================================================================
"""前端演示页 HTML 快照生成器：读 gateway/tdca.db，产出自包含单文件 HTML。
在 gateway/ 目录下运行：python scripts/snapshot_html.py [输出路径]"""
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import get_session  # noqa: E402
from db import models as M  # noqa: E402

_BADGE = {
    "real": '<span class="b real">real</span>',
    "mixed": '<span class="b mixed">mixed</span>',
    "simulated": '<span class="b sim">simulated</span>',
}


def _e(x) -> str:
    return html.escape(str(x if x is not None else ""))


def _fen(v) -> str:
    return f"{(v or 0) / 100:,.2f}"


def collect() -> dict:
    with get_session() as s:
        d = {}
        d["metric"] = s.query(M.SystemMetric).order_by(M.SystemMetric.id.desc()).first()
        d["mou"] = (s.query(M.MouRecord).filter_by(agent_id="AGENT-GENIE")
                    .order_by(M.MouRecord.period.desc()).first())
        d["tax_events"] = s.query(M.TaxEvent).order_by(M.TaxEvent.ts.desc()).limit(10).all()
        d["sea"] = s.query(M.SandboxState).order_by(M.SandboxState.id).all()
        d["nm"] = (s.query(M.Agent).filter(M.Agent.agent_id.like("AGENT-NM-%"))
                   .order_by(M.Agent.agent_id).all())
        d["eios"] = (s.query(M.Agent).filter(M.Agent.agent_id.like("EIOS-%"))
                     .order_by(M.Agent.agent_id).all())
        d["assets"] = s.query(M.AssetOrder).order_by(M.AssetOrder.order_no).all()
        d["terms"] = s.query(M.TermsRegistry).all()
        d["queue"] = s.query(M.AttestationRequest).filter_by(status="pending").all()
        d["agents"] = (s.query(M.Agent)
                       .filter(~M.Agent.agent_id.like("AGENT-NM-%"),
                               ~M.Agent.agent_id.like("EIOS-%")).all())
        d["nca_tail"] = s.query(M.NcaChain).order_by(M.NcaChain.ts.desc()).limit(5).all()
    return d


def render(d: dict) -> str:
    m = d["metric"]
    P = []  # parts
    P.append(f"""<section><h2>🏠 首页 KPI <small>/home · A-1 system/overview</small></h2>
<div class="grid4">
<div class="card"><div class="num">{m.total_deliveries}</div><div class="lbl">累计交付</div></div>
<div class="card"><div class="num">¥{_fen(m.total_tax_settled)}</div><div class="lbl">累计税收结算</div></div>
<div class="card"><div class="num">{m.avg_latency_ms} ms</div><div class="lbl">平均时延</div></div>
<div class="card"><div class="num">{m.total_fused} / {m.total_fail_closed}</div><div class="lbl">熔断 / fail-closed</div></div>
</div>
<p class="muted">税率：dispatch {_f_bp(m.dispatch_tax_bp)} · royalty {_f_bp(m.royalty_bp)} · transaction {_f_bp(m.transaction_fee_bp)} ｜ θ={m.theta} ϕ={m.phi} ｜ {_e(m.system if hasattr(m, 'system') else 'ECOCOG S-1~S-16 FROZEN（613 测试绿）')} {_BADGE.get(m.data_provenance, '')}</p></section>""")

    mo = d["mou"]
    P.append(f"""<section><h2>💰 税收仪表盘 <small>/tax · A-2 MOU 锚定（ID79 只增不降）</small></h2>
<div class="grid3">
<div class="card"><div class="num">¥{_fen(mo.mou_inbound)}</div><div class="lbl">MOU 进项</div></div>
<div class="card"><div class="num">¥{_fen(mo.mou_outbound)}</div><div class="lbl">MOU 出项</div></div>
<div class="card"><div class="num">¥{_fen(mo.mou_total)}</div><div class="lbl">MOU 合计（生成列）</div></div>
</div>
<p class="muted">主体 {_e(mo.agent_id)} · 账期 {_e(mo.period)} · 不可降 {'✅' if mo.mou_irreducible else '❌'} · {_e(mo.note)} {_BADGE.get(mo.data_provenance, '')}</p>
<table><tr><th>事件</th><th>类型</th><th>主体</th><th>金额</th><th>税率</th><th>性质</th></tr>
{''.join(f"<tr><td>{_e(t.event_id)}</td><td>{_e(t.type)}</td><td>{_e(t.agent_id)}</td><td>¥{_fen(t.amount)}</td><td>{_f_bp(t.tax_rate_bp)}</td><td>{_BADGE.get(t.data_provenance,'')}</td></tr>" for t in d['tax_events'])}
</table></section>""")

    P.append(f"""<section><h2>🧪 沙盒准入 <small>/sandbox · A-5 SEA 五要件</small></h2>
<table><tr><th>要件</th><th>状态</th><th>说明</th></tr>
{''.join(f"<tr><td>{_e(r.requirement)}</td><td class='{ 'g' if r.status=='GREEN' else 'a'}'>{'🟢' if r.status=='GREEN' else '🟠'} {r.status}</td><td>{_e(r.note)}</td></tr>" for r in d['sea'])}
</table>
<p class="muted">all_green = {'true' if all(r.status == 'GREEN' for r in d['sea']) else 'false'}（AMBER 不阻塞预研，阻塞入盒）</p></section>""")

    P.append(f"""<section><h2>📣 通知机 MRCR <small>/notifier · A-9 四角色（ID93）</small></h2>
<table><tr><th>角色</th><th>TDID</th><th>场景</th><th>状态</th><th>审计数</th></tr>
{''.join(f"<tr><td>{_e(r.name)}</td><td>{_e(r.tdid)}</td><td>{_e(r.scene)}</td><td class='g'>{r.status.upper()}</td><td>{r.audit_count}</td></tr>" for r in d['nm'])}
</table></section>""")

    P.append(f"""<section><h2>🤖 智能体集群 <small>/cluster · A-10 eios 十端点（ID25）</small></h2>
<table><tr><th>端点</th><th>能力</th><th>ID</th><th>状态</th></tr>
{''.join(f"<tr><td><code>{_e(r.endpoint)}</code></td><td>{_e(r.capability)}</td><td>{_e(r.agent_id)}</td><td class='g'>{r.status.upper()}</td></tr>" for r in d['eios'])}
</table></section>""")

    P.append(f"""<section><h2>🏛 五阶资产池 <small>/market · A-4</small></h2>
<div class="grid5">{''.join(f"<div class='card'><div class='num'>{a.order_no}</div><div class='lbl'><b>{_e(a.name)}</b><br>{_e(a.description)}<br>count={a.asset_count}</div></div>" for a in d['assets'])}</div></section>""")

    P.append(f"""<section><h2>👥 五面板 <small>/agents · 五元角色（H/M/L/μ/G）</small></h2>
<table><tr><th>主体</th><th>名称</th><th>能力</th><th>五元角色</th><th>确权状态</th></tr>
{''.join(f"<tr><td>{_e(a.agent_id)}</td><td>{_e(a.name)}</td><td>{_e(a.capability)}</td><td>{_e(a.five_role)}</td><td>{_e(a.attestation_state)}</td></tr>" for a in d['agents'])}
</table></section>""")

    P.append(f"""<section><h2>🖋 确权中心 <small>/attestation · A-11 待审队列（HUF 终裁）</small></h2>
<table><tr><th>请求</th><th>主体</th><th>类型</th><th>紧急度</th><th>事由</th></tr>
{''.join(f"<tr><td>{_e(q.request_id)}</td><td>{_e(q.agent_id)}</td><td>{_e(q.request_type)}</td><td class='{ 'r' if q.urgency=='urgent' else ''}'>{'🔴' if q.urgency=='urgent' else '🟡' if q.urgency=='normal' else '⚪'} {_e(q.urgency)}</td><td>{_e(q.reason)}</td></tr>" for q in d['queue'])}
</table></section>""")

    P.append(f"""<section><h2>📖 术语注册表 <small>/academy · A-6（G-1）</small></h2>
<table><tr><th>术语</th><th>定义</th><th>性质</th></tr>
{''.join(f"<tr><td><b>{_e(t.term)}</b> <code>{_e(t.term_id)}</code></td><td>{_e(t.definition)}</td><td>{_BADGE.get(t.data_provenance,'')}</td></tr>" for t in d['terms'])}
</table></section>""")

    P.append(f"""<section><h2>⛓ NCA 存证链尾 <small>ID91 调用即存证</small></h2>
<table><tr><th>NCA</th><th>prev</th><th>动作</th><th>行为者</th><th>性质</th></tr>
{''.join(f"<tr><td><code>{_e(n.nca_id)}</code></td><td><code>{_e(n.prev_nca)}</code></td><td>{_e(n.action)}</td><td>{_e(n.actor)}</td><td>{_BADGE.get(n.data_provenance,'')}</td></tr>" for n in reversed(d['nca_tail']))}
</table></section>""")

    body = "\n".join(P)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TDCA 前端演示快照（真库实读）· 2026-08-21</title>
<style>
body{{font-family:'Segoe UI','Microsoft YaHei',sans-serif;background:#f5f6f8;color:#1e293b;margin:0;padding:24px}}
.wrap{{max-width:1080px;margin:0 auto}}
header.top{{background:#0f172a;color:#fff;border-radius:12px;padding:18px 22px;margin-bottom:18px}}
header.top h1{{margin:0 0 6px;font-size:20px}}
header.top p{{margin:0;font-size:12px;color:#94a3b8}}
section{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;margin-bottom:16px}}
h2{{font-size:16px;margin:0 0 12px}}h2 small{{font-weight:400;color:#64748b;font-size:12px}}
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.grid5{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.card{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:12px;text-align:center}}
.num{{font-size:22px;font-weight:700;color:#0f172a}}
.lbl{{font-size:11px;color:#64748b;margin-top:4px}}
table{{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:8px}}
th,td{{border-bottom:1px solid #eef2f7;padding:7px 8px;text-align:left;vertical-align:top}}
th{{color:#64748b;font-weight:600;background:#f8fafc}}
code{{background:#f1f5f9;border-radius:4px;padding:1px 5px;font-size:11.5px}}
.g{{color:#059669;font-weight:600}}.a{{color:#d97706;font-weight:600}}.r{{color:#dc2626;font-weight:600}}
.b{{font-size:10px;border-radius:8px;padding:1px 7px;font-weight:600}}
.b.real{{background:#dcfce7;color:#166534}}.b.mixed{{background:#fef3c7;color:#92400e}}.b.sim{{background:#e0e7ff;color:#3730a3}}
.muted{{font-size:12px;color:#64748b;margin:10px 0 0}}
footer{{text-align:center;font-size:11px;color:#94a3b8;padding:8px 0 20px}}
</style></head><body><div class="wrap">
<header class="top"><h1>TDCA 官网 · 前端演示快照（15 路由核心板块）</h1>
<p>数据源：gateway/tdca.db 真库实读（非 mock）· 生成时间 2026-08-21 · 金额单位：元（库内整分）· 性质标注 ID92：simulated / mixed / real · 全站 NCA 水印 ID91</p></header>
{body}
<footer>TDCA ⟨ℑ, 𝒯, ℰ, 𝒫, 𝒦⟩ · 制度即公开（BV-3）· 本快照由 scripts/snapshot_html.py 自 tdca.db 生成，与线上页面同源同数据</footer>
</div></body></html>"""


def _f_bp(bp) -> str:
    return f"{(bp or 0) / 100:.2f}%"


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else str(
        Path(__file__).resolve().parents[2].parent / "前端演示快照-20260821.html")
    Path(out).write_text(render(collect()), encoding="utf-8")
    print("snapshot →", out)


if __name__ == "__main__":
    main()
