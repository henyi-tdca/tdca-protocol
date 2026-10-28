# TDCA-TEMPLATE-AUTH-001 · **Authorization Instrument Template** (English Human-Readable Version · `V1.0-FROZEN` · **Four Requirements** + **Fixed Format: Eight Fields**)

> Instrument ID: **TDCA-TEMPLATE-AUTH-001** ｜ Version: **`V1.0-FROZEN`** ｜ Date: **2026-10-03** (+08)
> Operation type: **Spec / Draft** ｜ Compiler: **Reasonix** (Think Tank · `L1-SI-103`) ｜ Nature: **In force (Phase-1 internal operation) (internal instrument · ⛔ not a judicial ruling)**
> **Authority (upstream)**: ⭐ `TDCA-SPEC-REGISTER-OF-RIGHTS-001` (draft *TDCA Registration System*, Article 12 **fixed format of the authorization instrument**, Article 11 **three requirements**) ｜ ⭐ `TDCA-AMEND-RULING-TDCRA-REG-001-001`~`-006` (four requirements and signature forms) ｜ ⭐ `TDCA-RULING-PHASE1-BUILD-PROPOSAL-003` §1.4 (P0: rewrite the authorization-instrument template against the four requirements)
> **Human-readable version (semantic authority)**: `TDCA-TEMPLATE-AUTH-001-授权件模板（中文人读版V1.0-FROZEN·四要件与固定格式八字段）.md` — ⚠️ **on conflict the Chinese human-readable version prevails**; ⛔ the machine-readable version may not be used to reverse-change semantics
> **Machine-readable version**: `TDCA-TEMPLATE-AUTH-001-授权件模板（机读版V1.0-FROZEN）.yaml` — ⚠️ the `locale.en: pending` flag recorded there is **satisfied as of this instrument** (⛔ the prior instrument is NOT amended; this instrument is the evidence)
> ⛔ Not for external use; ⛔ contains no credential values and no personal names; **time zone +08**

---

## 0. ⭐ One-line summary

⭐ This template is ⭐ **rewritten against the four requirements and laid out in the eight-field fixed format of Article 12** (⭐ submitting party / authorized party / scenario / scope of permission / term / tier / revenue share / revocation conditions); the four requirements (⭐ scenario constraint / five-tier asset form / full-composition authorized / legal-entity signature) are ⭐ **stated explicitly for every instrument**; special clauses and custom clauses are ⭐ **agreed by smart contract**; ⚠️ numeric items (⭐ revenue-share ratio / default term / tier ceiling) ⭐ **remain placeholders** (⭐ reserved to the founder); ⚠️ divergences from the counterparty-side template ⭐ **are registered** (⭐ §7 · ⛔ this side does not amend that instrument).

---

## 1. ⭐ Fixed format (⭐ eight fields · ⭐ per Article 12)

| ⭐ # | ⭐ Field | ⭐ Mandatory | ⭐ How to fill · boundary |
|---|---|---|---|
| `F1` | ⭐ **Submitting party** | ⭐ Required | ⭐ The rights holder or a submitter authorized by it; ⭐ must be a **legal entity**; ⛔ no agent may fill it in |
| `F2` | ⭐ **Authorized party** | ⭐ Required | ⭐ The receiving subject (⭐ agent / node / other); ⚠️ multi-tier sub-granting ⭐ listed tier by tier |
| `F3` | ⭐ **Scenario** | ⭐ **Required** (⭐ mandatory in the authorization-registration scenario) | ⭐ The owning scenario stated expressly; ⛔ **a scenario not stated ⛔ is outside the authorization scope** |
| `F4` | ⭐ **Scope of permission** | ⭐ Required | ⭐ Scope and action types that may be invoked / configured; ⛔ must not contain negative-space actions |
| `F5` | ⭐ **Term** | ⭐ Required | ⚠️ Start and end points; ⭐ if open-ended, it must expressly read "no term set" (⛔ may not be left blank) |
| `F6` | ⭐ **Tier** | ⭐ Required (⚠️ when sub-granting) | ⭐ The authorization tier of this instrument; ⚠️ **tier ceiling** ⭐ reserved to the founder |
| `F7` | ⭐ **Revenue share** | ⭐ Required | ⚠️ Consideration and revenue-share arrangement; ⚠️ **ratio value** ⭐ reserved to the founder; ⛔ this side does not fill in values |
| `F8` | ⭐ **Revocation conditions** | ⭐ Required | ⭐ Trigger and effective mode of revocation; ⭐ revocation ⭐ requires **the principal's own signature** |

> ⚠️ **Style**: ⭐ **all of them are authorization instruments** (⛔ no split between "self-authorization" and "third-party authorization"); ⭐ **the format is the same**; ⭐ special clauses and custom clauses ⭐ **are all agreed by smart contract** (⭐ subject fields ⛔ may not be customized).

---

## 2. ⭐ Four requirements (⭐ explicit per instrument · ⭐ lacking one, none holds)

| ⭐ # | ⭐ Requirement | ⭐ Corresponding block in this template | ⭐ Test |
|---|---|---|---|
| `R1` | ⭐ **Scenario constraint** | ⭐ `F3` Scenario | ⭐ **scenario mandatory** |
| `R2` | ⭐ **Five-tier asset form** | ⭐ Annex block "five-tier list" | ⭐ covered tiers must be listed; ⛔ tiers not listed may not be claimed under this instrument |
| `R3` | ⭐ **Full composition authorized** | ⭐ Declaration block "full-composition declaration" | ⭐ must declare that no undisclosed reservation exists; ⚠️ any reservation must be **stated expressly** ⟹ a reservation means **full composition is not reached** |
| `R4` | ⭐ **Legal-entity signature** | ⭐ Signature block | ⭐ signed by the **principal** (⭐ electronic signature / authorization code); ⛔ no agent may **sign, hold, or fill in** |

⭐ **Lacking one ⟹ the authorization does not hold** (⭐ `fail-closed`: ⭐ without an instrument, no configuration · ⭐ without authorization, no invocation).
⭐ **Own assets also require an instrument**: ⭐ whether the property is one's own or another's, ⭐ configuration ⛔ **must** carry this instrument.

---

## 3. ⭐ Template body (⭐ fill-in form · ⭐ English human-readable version)

```
[Authorization Instrument] TDCA-AUTH-<ID> | Version <V> | Data nature <REAL|SIMULATED>

1. Submitting party (F1): <legal entity name / identity label>       ※ no agent may fill in
2. Authorized party (F2): <receiving subject>                        ※ multi-tier sub-granting listed tier by tier
3. Scenario (F3)        : <owning scenario>                          ※ mandatory; a scenario not stated is outside scope
4. Scope of permission (F4): <invocable / configurable scope and action types>  ※ must not contain negative-space actions
5. Term (F5)            : <start> ~ <end>                             ※ open-ended must be stated expressly
6. Tier (F6)            : tier <n> (ceiling pending)                 ※ required when sub-granting
7. Revenue share (F7)   : <consideration and revenue-share arrangement> (ratio pending)  ※ numeric values reserved to the founder
8. Revocation conditions (F8): <trigger and effective mode>           ※ revocation requires the principal's own signature

[Four-requirement declaration]
  R1 Scenario constraint : same as F3 above
  R2 Five-tier asset form: <covered tiers: tier 1 / 2 / 3 / 4 / 5, listed item by item>
  R3 Full composition    : ☐ full composition declared; ☐ reservation exists (reserved items must be listed one by one)
  R4 Legal-entity signature: <principal's own signature · electronic signature or authorization code · signature event logged to NCA>

[Special clauses / custom clauses] = agreed by smart contract (⛔ not written into the eight subject fields)
[Reference and attestation] every reference and signature action is logged to NCA (subject / time / requirement-version hash / action type)
[Public-face mapping] after registration, published under four fields: ownership information / authorization information / authorization status / how to obtain
                       ※ "how to obtain" ≠ authorization already obtained
```

---

## 4. ⭐ Two forms (⭐ standard form / custom form)

| ⭐ Form | ⭐ Use | ⭐ Boundary |
|---|---|---|
| ⭐ **Standard form** | ⭐ Adopt the fill-in style of §3 directly | ⭐ the eight fields ⛔ may not be added to or deleted from; ⛔ field semantics may not be changed |
| ⭐ **Custom form** | ⭐ Draft separately for **special clauses** (⭐ e.g. graduated revenue share, conditional revocation) | ⚠️ must still contain the eight fields + four requirements; ⭐ special clauses ⭐ **agreed by smart contract** |

---

## 5. ⭐ Interface with admission and the panel

| ⭐ # | ⭐ Interface point | ⭐ Content |
|---|---|---|
| `1` | ⭐ **Admission** | ⭐ configuration-class invocations ⭐ require a **valid** instrument (⭐ admission gate); ⭐ invalid (⭐ revoked / requirement defect) ⟹ ⭐ **rejected** |
| `2` | ⭐ **Panel: five operations** | ⭐ pre-receipt / real-time authorization / additional authorization / license change / multi-tier authorization ⟹ ⭐ every operation ⭐ **must be instrumented** (⭐ a change is a new instrument version) |
| `3` | ⭐ **Status synchronization** | ⭐ authorization status ⭐ follows panel operations (⭐ pending / effective / changed / revoked / expired) |
| `4` | ⭐ **Multi-tier sub-granting** | ⭐ every tier ⭐ **requires an instrument and a signature**; ⭐ if any link fails ⟹ ⭐ **all its downstream links fail** |
| `5` | ⭐ **Exception** | ⭐ inside a sandbox and in drills ⛔ instrument exempt; ⚠️ **leaving the sandbox requires authorization** (⛔ no sandbox exit without authorization) |

---

## 6. ⭐ ⚠️ Reserved to the founder (⭐ placeholders · ⛔ this side does not decide)

| ⭐ # | ⭐ Item | ⭐ Handling in this template |
|---|---|---|
| `1` | ⚠️ **Revenue-share ratio** and form of consideration | ⭐ placeholder "ratio pending" |
| `2` | ⚠️ **Default term** (⭐ open-ended wording and default period) | ⭐ placeholder "open-ended must be stated expressly" |
| `3` | ⚠️ **Tier ceiling** and per-tier requirements | ⭐ placeholder "ceiling pending" |
| `4` | ⚠️ **Authorization-code validity** (⭐ one-time / reusable) | ⭐ placeholder (⭐ signature-form block) |

---

## 7. ⭐ Divergence register against the counterparty-side template (⭐ ⛔ this side does not amend it · changes go through `PR`)

| ⭐ # | ⭐ Item | ⭐ Counterparty-side instrument (⭐ read-only check · isolated worktree) | ⭐ This template | ⭐ Nature of divergence |
|---|---|---|---|---|
| `1` | ⭐ Four requirements | ⭐ **present** (⭐ scenario constraint / five-tier / full composition / legal-entity signature) | ⭐ present | ⭐ **aligned** (⭐ no conflict) |
| `2` | ⭐ **Eight-field fixed format** | ⚠️ **not laid out in eight fields** | ⭐ laid out in eight fields | ⚠️ **alignment needed** (⭐ this side issues an aligned version · ⛔ does not amend that instrument) |
| `3` | ⭐ **Term / tier / revenue share** | ⚠️ not listed separately | ⭐ listed separately (`F5` / `F6` / `F7`) | ⚠️ **gap filled** |
| `4` | ⭐ Public-face mapping | ⚠️ absent | ⭐ present (⭐ four fields) | ⚠️ **gap filled** |
| `5` | ⭐ Drafting attribution | ⚠️ reads "institutional drafting group" | ⭐ drafted by this side (think tank) | ⭐ **attribution convention** (⭐ per registered precedent) |

> ⚠️ **Disposition**: ⭐ this instrument ⭐ serves as the **aligned version** only; ⚠️ whether the counterparty-side instrument needs to be changed to align ⟹ ⭐ changes to a counterparty-side instrument ⭐ **must go through `PR` / a work order** (⛔ this side does not amend it).

---

## 8. ⭐ Boundaries and self-check

1. ⭐ This instrument is an **in-force template** (⭐ `V1.0-FROZEN` · ⛔ not a judicial ruling · **Phase-1 internal operation**); ⛔ it **amends** no registered instrument, no counterparty-side instrument and no in-repo instrument (⭐ **append-only**); changes go through `PR`.
2. ⛔ **Zero external exposure**; ⛔ this side has **not pushed, not merged, not deployed, not logged in, not handed over**; ⛔ **no credential values and no personal names**; **time zone +08**.
3. ⛔ Does not decide thresholds / weights / bars / scale / signing authority / **institution-layer semantics** on the founder's behalf; ⛔ **no mathematical content, no legal opinion, no legal determination**.
4. ⚠️ **Faithful registration**: ⭐ the eight fields ⭐ follow the `P0-3` note and Article 12 (⭐ field names transcribed); ⭐ the four requirements ⭐ follow the registered amendments; ⚠️ numeric items ⭐ **remain placeholders** (⭐ this side has not set them); ⚠️ divergences from the counterparty-side instrument ⭐ **read-only checked by this side** (⭐ §7).

---

*TDCA-TEMPLATE-AUTH-001 V1.0-FROZEN: **Authorization Instrument Template** (English human-readable version) — ⭐ **eight-field fixed format** (⭐ submitting party / authorized party / scenario / scope of permission / term / tier / revenue share / revocation conditions) + ⭐ **four requirements stated per instrument** (⭐ lacking one, none holds) + ⭐ **two forms** (⭐ standard / custom · ⭐ special clauses agreed by smart contract) + ⭐ interface with admission and the five panel operations + ⭐ public-face four-field mapping | ⚠️ 4 items pending (⭐ revenue-share ratio / default term / tier ceiling / authorization-code validity) | ⚠️ 5 divergences from the counterparty-side instrument (⭐ registered only · ⛔ not amended) | ⛔ **NOT IN FORCE** | Compiled by: Reasonix (`L1-SI-103`)*
