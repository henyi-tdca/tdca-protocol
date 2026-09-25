# Simulated End-to-End Validation Report (Simulated)

> Nature: an **experimental simulation report**. It does **not** prove that any institution is effective
> and does **not** replace a real controlled trial. All data are **SIMULATED**.
> ⚠️ This public version contains **no result numbers**; only method, settings and qualitative observations
> are kept. Full numbers and re-runnable artifacts ship with the internal version.

## 1. What is validated (NOT institutional effectiveness)
Criteria and flow are executable and produce output; the three arms (bare / conventional guardrail /
gatekeeper) show a clear qualitative distinction; **three gaps** were found.
Explicitly out of scope: proving institutional effectiveness, proving criteria correctness, or replacing a
real controlled trial. Zero network, zero quota, zero external side effects.

## 2. Settings and **assumed** parameters (all assumed, NOT measured)
Assumed probabilities: hard-item touch in ordinary tasks **0.02**; in boundary tasks **0.85**;
conventional-guardrail hit rate **0.45**; semantic-decision interception rate **0.90**; rule-decidable
interception set to **1.0**. Deterministic random source (**re-runnable**); not a real workload trace.
> The above is **design settings**, not results. Result numbers are omitted here.

## 3. Results (qualitative)
Bare arm: highest share of severe overruns, no replayable samples. Conventional-guardrail arm: only a
**small** improvement (recognises known signatures only). Gatekeeper arm: **zero** severe overruns and the
highest replayability — but that zero **depends on two preconditions** (Finding 3) and partly arises from
**circuit-breaker fallback** (Finding 1). Logs ≠ replayability.

## 4. Three findings
1) The criteria hide an intermediate state: "reached the network, then cut by the breaker" ≠ "blocked before
egress"; the former already has external side effects. Add a separate tier "breaker fallback after egress"
(reported, not counted as severe, must be disclosed); for **irreversible egress writes** require a
**pre-egress interception rate of 1.0**.
2) "Rule-decidable" and "semantically decidable" are not separated: with semantic items counted together the
goal "severe overrun rate = 0" is unreachable. Options: move them out of the severe tier; add a human review
channel; or restate the goal as rule-decidable = 0.
3) The gatekeeper "zero" depends on two preconditions; never report "zero" without stating them.

## 5. Four open recommendations
As listed above (add the tier; require 1.0 pre-egress for irreversible items; decide semantic treatment;
require preconditions alongside any "zero").

## 6. Limitations
Fully simulated; parameters assumed; logical-level reproduction only; no fault injection; no cloud stage.

## 7. Conclusion
Executable, deterministic, re-runnable; arms qualitatively distinct; three gaps found ⟹ criteria need
revision before any real run.
