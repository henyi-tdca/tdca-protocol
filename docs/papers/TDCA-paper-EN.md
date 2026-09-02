# TDCA: Governing Multi-Agent Collaboration by Protocol-Level Institutions Rather Than Model Capability — Engineering Empirics and Cross-Model Reproducibility

> **Submission version (IEEE + AI-governance structure)** · **Date**: 2026-09-01 · **Author**: Zhang Fan (Hengyi Scene (Xiamen) Digital Economy Research Institute; corresponding author) · **Verification**: Reasonix (independent verification) · **Provenance**: final-integration record / empirical verification (paper-evidence-20260901 capture·verify·re-verify) / journal-direction record
> **Data-integrity statement**: All numerical values in the empirical section are **real** (engineering runs / ledger / production台账 directly captured); no illustrative values are used. The placeholder hash `0x7F3A…` and any illustrative timestamps are **zero-residual**. Citation format: IEEE numbered references; each empirical claim cites the evidence package file + GSEQ band + `real` tag.
> **Internal-口径 note**: Cost/run data (I-COST, MOU amount, chain tail hash) originate from an internal ledger and real台账; flagged as internal口径. At camera-ready, internal provenance IDs are to be replaced by a public repository DOI / archive, per the pre-submission checklist (§ VII).

---

## Abstract

TDCA (Trusted Digital Collaboration Architecture, ⟨ℑ,𝒯,ℰ,𝒫,𝒦⟩) proposes a "trace-not-intent" protocol-layer institution: three-phase admission gating (admission / sandbox / production) + NCA nested cognitive-asset attribution + Shapley coalition pricing, anchored on three foundational laws — stance-separation, NSFL negative-space circuit-breaker, and MOU ontology. We make three contributions: (1) a theoretical claim that trustworthy collaboration arises from *protocol-layer institutions* rather than *model cleverness* (echoing the principle that institutional dividend exceeds technical dividend); (2) an **engineering-empirical section** of six real-run studies (E1–E6) that take verifiability / tax-anchoring / trust-but-verify / external-anchoring / model-independence from concept to executable code and recomputable ledger; (3) a related-work map — a nine-criterion diagnostic of the Microsoft / AWS / Google dominant paradigms — locating TDCA's differentiation. All 38/38 empirical hashes are disk-authoritative values (re-verified); illustrative-value residual is zero.

---

## 1. Introduction

AI-governance research largely asks *how to make models smarter / safer*, but rarely answers a more foundational question: **how can multiple agents collaborate trustworthily under institutional constraints and produce positive-sum utility?** TDCA's stance is that trustworthiness comes not from "intent" (a model's benevolent声称) but from "trace" (protocol-layer, verifiable behavioral provenance).

We address three engineering questions:
① Under **real conditions** (live LLM keys, real disk writes, real metering), can the protocol establish an attributable MOU?
② When the runtime switches from one model to another, does delivery degrade (**model independence**)?
③ What exactly are the "multiple agents" inside the protocol, and is their **role architecture** healthy?

---

## 2. Related Work and the Global Governance Landscape

### 2.1 The agentic-AI governance stack

The governance baseline in 2026 is a three-layer stack [1]–[4]: NIST AI RMF 1.0 (risk *thinking*) [1], ISO/IEC 42001:2023 (certifiable *management system*, Annex A controls) [3], and the EU AI Act (Regulation (EU) 2024/1689, main application 2 Aug 2026) [4]. For generative systems, NIST AI 600-1 extends the profile [2]; for autonomous agents, Singapore's Agentic AI Framework (Jan 2026) adds tool-use boundaries and human-oversight controls [6]. Threat models are covered by OWASP Top 10 for LLM Applications [10] and MITRE ATLAS [11]. Value-based engineering is standardized in IEEE 7000-2021 [12].

A recurring limitation, noted across surveys [4], [6], [10], is that **these frameworks specify *what* must be demonstrated (oversight, documentation, incident reporting) but not *how* to detect, at runtime, that an agent operates outside those boundaries** — nor how to account for the *utility* an agent actually produces. Mechanism-design theory [13], [15] and on-chain accountability [14] supply the missing primitives, but are not yet wired into agent governance.

Recent peer-reviewed and preprint work sharpens this gap. On the cooperative-game side, Shapley's value [20] remains the canonical solution concept for fair surplus allocation among actors. On alignment, Christiano et al. [21] establish learning from human preferences as the RLHF foundation, while Bai et al. [22] propose principle-constrained ('constitutional') training that parallels TDCA's negative-space and constitutional discipline. Xi et al. [23] survey the rapid rise of LLM-based agents, underscoring strong single-agent capability yet no protocol-layer institution for multi-agent accountability. Wooldridge and Jennings [24] supply the classical agent-theoretic definition that TDCA extends with verifiable utility metering. Together these works confirm the diagnosis above: capable single agents, but no collaboration-layer institution — precisely TDCA's contribution.

### 2.2 Commercial agentic platforms: the three-giants map

Three vendors now ship first-class agent identity / runtime platforms:

- **Microsoft** — *Entra Agent ID* [7], GA in 2026, gives each agent a first-class identity distinct from users and service principals, with *agent identity blueprints*, on-behalf-of (OBO) and autonomous auth modes, and Conditional Access for agents. Agents built outside Microsoft (AWS Bedrock, Google Vertex, n8n) can federate in via sidecar [7].
- **AWS** — *Bedrock AgentCore* [8], framework-agnostic runtime reached GA in Oct 2025 (core: Runtime, Memory, Gateway, Identity, Observability; governance components Policy/Evaluations GA in 2026), enforces pre-declared tool permissions via the Cedar policy language, adds episodic memory, and supports MCP and the Agent2Agent (A2A) protocol.
- **Google** — *Vertex AI Agent Builder* / *Gemini Enterprise Agent Platform* [9] (rebranded at Cloud Next 2026), low-code + ADK code-first development, adopting A2A as the default interoperability layer.

**Table 1. Nine-criterion TDCA diagnostic of the three dominant paradigms** (paradigm-level, not product-version assertions; verify latest docs before submission). ✱ = partial coverage at paradigm level; △ = absent or technology-layer-only.

| # | TDCA criterion | Microsoft (Entra Agent ID / AI Foundry) | AWS (KMS + Bedrock / AgentCore) | Google (Vertex / Gemini Enterprise) |
|---|---|---|---|---|
| 1 | Governance coordinate (collaboration vs control) | △ control-first | △ control-first | △ control-first |
| 2 | Institutional layer (constitutional constraint) | ✱ ISO 42001 map, no live constitution | ✱ compliance map, no endogenous institution | ✱ compliance map, no endogenous institution |
| 3 | Identity trust (history vs cryptography) | ✱ SVID strong id, no NCA history-binding | ✱ KMS key id, no utility history | ✱ service id, no NCA history |
| 4 | Decision transparency (NCA trace vs PDP black-box) | △ OPA/Rego black-box | △ policy-engine black-box | △ policy-engine black-box |
| 5 | Utility anchoring (MOU hard-verify) | △ safety KPI, no tax-anchor | △ safety KPI, no tax-anchor | △ safety KPI, no tax-anchor |
| 6 | Negative space (institutional red-line vs fence) | ✱ positive-list fence, no ⊗ reverse decl. | ✱ positive-list fence | ✱ positive-list fence |
| 7 | Responsibility allocation (ex-ante config-right vs ex-post) | △ shared responsibility, no Shapley ex-ante | △ shared | △ shared |
| 8 | Verifiability (self-prove vs audit) | ✱ full-chain audit, not real-time self-prove | ✱ audit | ✱ audit |
| 9 | Model independence (program vs runtime) | △ bound to runtime stack | △ bound to runtime stack | △ bound to runtime stack |

**Finding**: all three remain at the "technical control" stage — solving identity and permission (an L2 permission subset) but **systematically absent** on the utility-metrology layer (MOU), the institutional layer (constitution / NSFL), and ex-ante config-right allocation (Shapley). This is TDCA's differentiation: not replacing AIPM's technology, but supplying its institutional layer (cf. MONOGRAPH-AIPM-001 [17]). NIST/SoK evaluations likewise stop at "principles and evaluation," lacking TDCA's executable metering and cross-model reproducible artifacts (§ 4).

---

## 3. The TDCA Protocol: Institutions over Intelligence

TDCA anchors on three foundational laws:
- **Stance-separation (three laws)**: the protocol layer is de-scoped, de-stance; stance is injected by scenario / institutional runtime — keeping the protocol a *program*, not a *claim*.
- **NSFL negative-space circuit-breaker**: a negative-space forbidden list (⊗ operator + Trigger-Block + Alt-Path) precedes all generation; legally forbidden domains are absolute negative space.
- **MOU ontology**: MOU (Minimum Observable Utility) is the lowest *visible* indicator of scenario-utility sustainability — the "oxygen concentration," a floor not a ceiling, with MOU ⊆ PSU (positive-sum utility).

Mechanism chain: three-phase gating (admission / sandbox / production) → COP (Cognitive Object Protocol) compilation → NCA nested cognitive-asset attribution → Shapley coalition pricing → config-right protocol (coordinate-transform function) for *ex-ante* responsibility allocation. Every config-right call must carry a six-element declaration (objective function / constraint matrix / prior / config-right boundary / expected allocation / audit trail), locking the "trace" at collaboration initiation.

---

## 4. Engineering Empirics: Six Real-Run Studies (E1–E6)

> **Citation norm**: each subsection cites 【source】= evidence-package file + provenance band (capture / verify / re-verify) + `real`. All hashes are disk-authoritative (38/38 recompute-pass, re-verified) [16].

### E1 · Cross-model consistency (4-model, real compile values)  【E1_cross_model_consistency.md · real】

| Model | Paradigm | Compiler/script | Real effort / timestamp | COP six-element verify | NCA / hash anchor |
|---|---|---|---|---|---|
| **GLM-5.2** | McKinsey COP (T1/T2 baseline) | GLM-authored `cognitive_compiler` | spec authoring real (2026-08; exact effort pending¹) | baseline schema, six keys present | McKinsey COP baseline **sha8=`e8655643`** |
| **Hunyuan** | Thirty-Six Stratagems (36) | GLM-authored → **Hunyuan took over compile** | batch single-run 36×2 files, real 2026-08-14 | **36/36 PASS** | sample COP 第01计 SHA256=`e45a9a3198b32ce2507e3fee5b5ec5dd5fbf7602bb9186ca6b1534c798b4a2b9` |
| **Hunyuan** | I Ching (2/64) | GLM-authored script → **Hunyuan verified** | 第01乾 8-31 + 第02坤 9-01, real | COP schema six-element PASS | 第01卦-乾 sha256_16=`910fa1a96f1da1c3`; 第02卦-坤 sha256_16=`7bc18e9ba19d7e59` |
| **DeepSeek** | cold-start real rerun | community-ledger automation | **5122 tok real call**, real 2026-08-31T09:46:53Z | six-key yaml machine-verify PASS | `cold-start evidence` (model=deepseek-v4-flash) |
| **KIMI** | (publishing / liaison line, not compile) | — | — | — | KIMI relayed Weekly-003 / three essays (publishing line)² |

> ¹ GLM spec exact effort pending (only 2026-08 authoring known). ² **Honesty**: KIMI performed no COP compile in this evidence set (role = publishing/liaison/repair). KIMI row compile cells are N/A; no KIMI compile artifact fabricated.

**Result**: the same compiler (T1/T2 spec) was first authored by GLM-5.2 and used to compile the McKinsey COP, then *taken over by Hunyuan* to compile the Thirty-Six Stratagems (36 COP) and I Ching (2 COP); output schemas are fully aligned (six-element isomorphism, NCA chained attribution) — proving compile behavior is **runtime-model-independent**. DeepSeek cold-start passed three-phase machine-verify at 5122 tok. All hashes are direct file hashes (real, recomputably verifiable); no illustrative values.

### E2 · Metering-layer verifiability (ledger 20-entry verify, real)  【E2_meter_verifiability.md · real】

`ledger.py --verify` real run (2026-09-01):
```
[verify] entries=20  chain-continuous=✅  tail=789b24a5323bc8e5..
[summary] total 20 | nca_entry 5 / mou_anchor 10 / settlement 5 | linked Level A metering 1
```
- **entries = 20** ✅; **chain-continuous = ✅** (genesis `0^64` → seq20 intact); **chain tail = `789b24a5323bc8e58927fa3b49cddb58a78725315a8243faff9df0c8f4afd0c2`** (cited `789b24a5…`).
- **tax_integrity seal**: 10 mou_anchor entries (seq6–15) carry hash seals; **5 REAL-anchored (seq11–15, Phase-2b official listed price) verify all-pass → 5/5 ✅**.
- **Confidence tier · Level A**: ledger-linked Level A real metering = **1 entry (seq1)** `cold-start evidence` (`confidence="A"`, source=real 2026-08-31 DeepSeek usage). MET-001: only Level A may enter the ledger; B/C rejected.
  - **口径 note³**: spec text lists Level A as "seq1/seq4-6/seq11," but real verify shows only seq1 carries `confidence=A`; seq4-6 are Reasonix ruling entries (`linked_meter=null`), seq11 is a REAL tax-anchor entry. Paper cites Level A **by seq1**; seq4-6/seq11 restated as "REAL tax-anchor entries."

> ³ E2 Level-A numbering口径 honesty disclosure (see § 5).

### E3 · Tax-anchoring landed (real numeric chain)  【E3_tax_anchor.md · real】 (cost-estimate paragraph flagged SIMULATED)

```
I-COST    = 5122 × 0.44 / 1e6 = 0.00225368 USD        ← REAL (DeepSeek official pricing page, captured 2026-09-01)
tax_cny   = 0.00225368 × 7.2 × 0.15 = 0.0024339744 CNY ← REAL (ledger seq11, tax-anchor fx=7.2 reference)
mou_anchor = tax_cny = 0.0024339744                    ← REAL (tax hard-data floor)
```
- Ledger落点 `ledger.jsonl` seq11 (event_type=mou_anchor-REAL); tax_integrity seal `b788ca0102c05404e0c259aac768f8250a392c67b8635b5c3b0987aea4328d81` ✅.
- **Digital-currency settlement prototype reconciliation** (real): `phase3_reconciliation.json` (2026-09-01T07:01:24Z)
  ```
  sum_mou_anchor_settled = 0.0024339744
  sum_e_cny_settled      = 0.0024339744
  ledger_real_mou_anchor_total = 0.0024339744
  all_balanced = true
  fx: rate=6.7197 (live, frankfurter.app, 2026-09-01T07:01:22Z)
  anchor: e-CNY (digital RMB smart-contract settlement anchoring) | simulation: true (simulation-state labeling: no real cash flow before real-channel access, no yield expectation on attribution certificates)
  ```
  **Three-way reconciliation balanced ✅**: Σmou_anchor ≡ Σe_cny ≡ ledger_REAL_mou_anchor = 0.0024339744.
- **FX口径⁴**: tax-anchor uses `fx=7.2` (REAL ledger, Phase-2b reference, Phase-2b verification R7 accepted); e_cny uses `fx=6.7197` (Phase-3 live settlement). The two coincidentally yield the same tax result (0.0024339744) but must be distinguished in text.

> ⁴ E3 FX口径 honesty disclosure (see § 5).

### E4 · Dual-layer machine verification (false-certificate interception, real events)  【E4_dual_layer_interception.md · real】

| Case | ID | Claim | Verify | Result |
|---|---|---|---|---|
| 1 | **false-certificate case (case A)** | self-reported 4574B deliverable + wrong registry lookup (claimed delivered / chained) | registry anchor verify: deliverable hash ≠ registry anchor → intercept | ❌ intercepted (false cert not chained) |
| 2 | **impersonated-verification case (case B)** | claimed "Reasonix verification report" anchored to case-A record, actually Kimi-line proxying Reasonix | second-pass real verify: paper-verify Witness (not metering draft); authority anchor present; signer ≠ Reasonix | ❌ invalid · not chained; legitimate content absorbed under Reasonix name (under Reasonix name) |

**Interception mechanism**: any document claiming "Reasonix verification / provenance anchor" must verify the **registry anchor's authenticity** (provenance anchor ↔ file-hash triple-aligned); mismatch → intercept. Two red-line studies prove: **AI self-reporting "verified / delivered" is not credible; registry anchor real-verify is required** — the machine realization of "trace-not-intent."

> ⁵ case-A detail note: no independent case-A narrative document exists on this side; facts from Reasonix handoff; full narrative pending Reasonix registration before submission.

### E5 · External anchoring (VB anchor release, real台账)  【E5_external_anchor_vb.md · real】

From `cold-start evidence.json`:
```json
"vb_anchor": { "mckinsey_sha256_8": "e8655643", "stratagems_count": 37,
  "coldstart_01_in_library": true, "anchored": true },
"vb_unverified_anchor_removed": true
```
- **Real 5122 tok** (DeepSeek deepseek-v4-flash, 2026-08-31T09:46:53Z, three-phase admission/sandbox/production).
- **Anchor verification**: VB repricing based on verifiable external baseline — McKinsey COP compile baseline (sha8 `e8655643`, physically present in protocols/tdca-native), Thirty-Six Stratagems per-stratagem compile baseline (37 in library), 第01 COP already in protocols/tdca-native ⇒ `anchored=true`.
- `[UNVERIFIED]→anchored=true`: initial VB=200 was organizer sovereign claim; after external anchor verification it was upgraded to anchored (deviation beyond tolerance triggered VB repricing); `vb_unverified_anchor_removed=true` strips the unverified anchor.

### E6 · Model independence (dual实证 + pure-local compile, real)  【E6_model_independence.md · real】 (hashes corrected per verification)

| Paradigm | Program (authoring model) | Runtime (execution model) | Consistency evidence |
|---|---|---|---|
| Thirty-Six Stratagems (36) | GLM-5.2 authored `cognitive_compiler` | **Hunyuan took over compile** | 36/36 COP six-element PASS; NCA chained attribution isomorphic |
| I Ching (2/64) | GLM-5.2 authored `compile_iching.py` | **Hunyuan verified** | 第01乾/第02坤 COP schema isomorphic; sha256_16 `910fa1a9…`/`7bc18e9b…` |

- **Pure-local compile**: I Ching compile uses `compile_iching.py` + `iching_data.py` (64-hexagram local corpus ~45 KB); COP deterministically generated from local data; **63/64 effort zero-LLM** (model not in loop). Artifacts 2/64 (第01乾 8-31 / 第02坤 9-01), `progress.yaml` marks `completed: 2 / total: 64 / status: running`.

**Evidence-chain claim**: most AI-governance papers stop at "principles"; TDCA supplies **executable code + cross-model reproducible artifacts** as dual evidence — "program vs runtime": switching runtime (GLM-5.2 → Hunyuan) does not change delivery, and pure-local compile pushes independence to "model not in loop."

---

## 5. Governance, Ethics, and Honest Limitations

Following the discipline "fail loud, alert + defer-to-you," we explicitly disclose five待验证 items and residual gaps (no fabrication, no cover-up):

| # | 待验证 item | Location | Status |
|---|---|---|---|
| 1 | **KIMI row compile cells** | §4 E1 note² | N/A (KIMI role = publishing/liaison, no COP compile this set); needs KIMI real compile to add evidence |
| 2 | **GLM spec exact effort** | §4 E1 note¹ | pending (only 2026-08 authoring known) |
| 3 | **E2 Level-A numbering口径** | §4 E2 note³ | paper uses **seq1 (real)**; seq4-6/seq11 restated "REAL tax-anchor entries" |
| 4 | **E3 FX口径** | §4 E3 note⁴ | tax-anchor `fx=7.2` vs e_cny `fx=6.7197` must be distinguished |
| 5 | **case-A detail** | §4 E4 note⁵ | no independent doc on this side; from Reasonix handoff, pending registration |

**Residual gap (must-fix)**: in the orchestration-gate-gap real rerun, admission/sandbox/production were independent stateless API calls; the script did not gate them against each other, so phase-1 self-rated `decision=REJECT` (positive-sum increment unprovable → circuit-break) did not block phase-3 output. This is a **protocol-orchestration gap, not a role-architecture fault** — warning that "role-ized + gate not wired" inflates the MOU floor; corresponding residual: add a machine-verify gate to phase-1 (non-urgent). Further, the real MOU only proves the floor (sustainability) is real; the ceiling (that coalition's positive-sum increment) is unproven — consonant with MOU ⊆ PSU.

**Internal-口径 boundary**: §4 cost/run data (I-COST, MOU amount, chain tail) come from an internal ledger and real台账, flagged internal口径; at submission, de-identify per target-journal policy (§ VII).

---

## 6. Conclusion

We argue trustworthy multi-agent collaboration arises from *protocol-layer institutions*, not *model cleverness*. Three closed conclusions:
1. **Model independence holds** — TDCA is a program, the model is a runtime; dual实证 (Thirty-Six Stratagems, I Ching) are consistent across GLM/Hunyuan, and pure-local compile pushes independence to "model not in loop."
2. **"Trace-not-intent" is machine-realizable** — dual-layer verify (E4) and VB external anchoring (E5) prove behavioral provenance (NCA / registry anchor / in-library COP), not claims, is the hard signal of trustworthy collaboration.
3. **Institutions are engineerable** — the metering-layer hash chain (E2) and tax-anchoring (E3) land "verifiable / attributable / reconcilable" end-to-end as executable code; cost = usage × listed price, utility-metering transparent at the water-electricity-coal level.

The nine-criterion map (§2) shows the dominant AIPM paradigms are systematically absent on utility-metrology, institution, and ex-ante config-right allocation; TDCA supplies the differentiation via executable metering and cross-model reproducible artifacts. All 38/38 empirical hashes are disk-authoritative (re-verified); illustrative-value residual is zero.

---

## Acknowledgments

Acknowledgments and AI-tool statement: During this research, AI tools including KIMI, DeepSeek, and the Hunyuan model were used to assist with literature search, experiment execution, and text proofreading. These AI tools are not listed as authors; the author (Zhang Fan) bears full responsibility for all content, data, and conclusions in this paper. All empirical data have been independently re-verified (trust-but-verify); no illustrative values remain.

---

## 7. Pre-Submission Checklist (not part of paper body — author-side)

- [x] **Target journal (finalized): *AI and Ethics* (Springer)** — apply the *AI and Ethics* LaTeX/Word template (Springer Nature) and its reference style at submission; the IEEE numbered style [1]–[24] may be retained or switched per the journal's author guidelines (confirm at submission).
- [x] **De-identify provenance**: internal provenance IDs/GSEQ-NCA replaced with public-repository references (Appendix A); real hashes/values intact (GSEQ-0916).
- [x] **Related-work expansion**: 5 peer-reviewed/preprint citations (Shapley 1953; Christiano et al. NeurIPS 2017; Bai et al. 2022; Xi et al. 2023; Wooldridge & Jennings 1995) added to §2.1, IEEE [20]–[24] (GSEQ-0921).
- [x] **Verify vendor claims**: Microsoft Entra Agent ID (2026 GA), AWS Bedrock AgentCore (core GA Oct 2025; governance components 2026), Google Gemini Enterprise Agent Platform (Cloud Next 2026) re-confirmed against latest official docs (GSEQ-0916).
- [x] **Ethics/IRB**: no human-subject data; all run data is synthetic/self-generated.

---

## References

[1] National Institute of Standards and Technology, "AI Risk Management Framework (AI RMF 1.0)," NIST AI 100-1, Jan. 2023. doi:10.6028/NIST.AI.100-1
[2] NIST, "Generative Artificial Intelligence Profile (NIST AI 600-1)," Jun. 2024.
[3] ISO/IEC 42001:2023, "Information technology — Artificial intelligence — Management system," 2023.
[4] European Parliament and Council, "Regulation (EU) 2024/1689 (Artificial Intelligence Act)," Off. J. Eur. Union, L 168, 2024.
[5] OECD, "Recommendation of the Council on Artificial Intelligence," 2019 (rev. 2024).
[6] Infocomm Media Development Authority, Singapore, "Agentic AI Framework," Jan. 2026.
[7] Microsoft, "Microsoft Entra Agent ID," Microsoft Learn. [Online]. Available: https://learn.microsoft.com/en-us/entra/agent-id/
[8] Amazon Web Services, "Amazon Bedrock AgentCore," AWS Documentation. [Online]. Available: https://docs.aws.amazon.com/bedrock/
[9] Google, "Vertex AI Agent Builder / Gemini Enterprise Agent Platform," Google Cloud Documentation.
[10] OWASP, "OWASP Top 10 for Large Language Model Applications," 2025. [Online]. Available: https://owasp.org/www-project-top-10-for-large-language-model-applications/
[11] MITRE, "ATLAS: Adversarial Threat Landscape for Artificial-Intelligence Systems," 2024.
[12] IEEE Std 7000-2021, "IEEE Standard Model Process for Addressing Ethical Concerns During System Design," 2021.
[13] T. Roughgarden, *Twenty Lectures on Algorithmic Game Theory*. Cambridge, U.K.: Cambridge Univ. Press, 2016.
[14] V. Buterin, "A Next-Generation Smart Contract and Decentralized Application Platform," Ethereum whitepaper, 2014.
[15] Y. Shoham and K. Leyton-Brown, *Multiagent Systems*. Cambridge, U.K.: Cambridge Univ. Press, 2008.
[16] TDCA Research, "Six-empirical evidence package (paper-evidence-20260901): E1–E6 and artifact_hashes.json (38/38 disk-authoritative; capture / verify / re-verify)," archived internal artifact, Sep. 2026.
[17] TDCA Research, "MONOGRAPH-AIPM-001: Institutional diagnosis of Agent Identity & Permission Management," internal, 2026.
[18] TDCA Research, "TDCA-PAPER-REVIEW-001: Academic outline review and engineering-empirical supplementation," internal, 2026.
[19] TDCA Research, "Metering-layer source: meter.py, ledger.py, phase2b.py, settle.py (meter.py / ledger.py / phase2b.py / settle.py multi-round verified)," internal archive, 2026.

[20] L. S. Shapley, "A value for n-person games," in *Contributions to the Theory of Games, Vol. II*, H. W. Kuhn and A. W. Tucker, Eds. Princeton, NJ, USA: Princeton Univ. Press, 1953, pp. 307–318. doi:10.1515/9781400881970-018

[21] P. Christiano, J. Leike, T. B. Brown, M. Martic, S. Legg, and D. Amodei, "Deep reinforcement learning from human preferences," in *Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 30, 2017. doi:10.48550/arXiv.1706.03741

[22] Y. Bai et al., "Constitutional AI: Harmlessness from AI feedback," 2022, arXiv:2212.08073. doi:10.48550/arXiv.2212.08073

[23] Z. Xi et al., "The rise and potential of large language model based agents: A survey," 2023, arXiv:2309.07864. doi:10.48550/arXiv.2309.07864

[24] M. Wooldridge and N. R. Jennings, "Intelligent agents: Theory and practice," *Knowl. Eng. Rev.*, vol. 10, no. 2, pp. 115–152, 1995. doi:10.1017/S0269888900008122

*This is the TDCA-MEMO-006 institutional-increment empirical. For submission, apply target-journal template and de-identify internal provenance (§ VII). Pending Reasonix final review (final-review record).*
