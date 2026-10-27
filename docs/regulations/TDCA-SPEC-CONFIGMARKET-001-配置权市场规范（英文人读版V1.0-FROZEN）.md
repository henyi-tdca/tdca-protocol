# TDCA-SPEC-CONFIGMARKET-001 · **Configuration-Right Market Specification** (Single Authoritative Draft · English Human-Readable Version · `V1.0-FROZEN (IN FORCE)`)


---

## 0. One-line summary

This draft is **rewritten from the class-`A` master text**, aligned clause by clause with current registered positions per the `P9` reconciliation instrument: it adopts the **self-sufficient form that does not depend on external parties** ( rights confirmation = registration; signature = the legal entity itself) ＋ **an explicit migration slot reserved** ( to be migrated once external counterparts are connected); it closes three gaps — **the two-way registration split / the four authorization requirements / the four public-face fields**; all **rates, thresholds and parameter values** **are transcribed from the old instrument and marked "pending founder review"** ( this side does not decide them); mathematical content **only points to annexes** ( no formulas are transcribed). Scope of incorporation **this one instrument** ( the remaining class-`A` **12** instruments serve as **annexes** · see §9).

---

## 1. General provisions

**Article 1 (Purpose)** This specification governs the **`L2` configuration-right market**: admission, registration, authorization, publicity, trading, settlement, dispute and exit ( **inheriting the old general specification's "general provisions + three chapters" style**).

**Article 2 (Scope)** Applies to **internal operation of this site** ( phase one · internal live run); external launch requires a separate founder instruction ( governed by the effectiveness and withdrawal of the public face).

**Article 3 (Two root positions)**
1. **No external dependency**: for any action that would depend on external parties, the current **self-sufficient form** applies ( rights confirmation = registration; signature = the legal entity itself; settlement = `SIMULATED`).
2. **Migration slot reserved**: once external counterparts are connected, **migration proceeds slot by slot** ( see §7 · requirements and effect hierarchy unchanged).

**Article 4 (Four basic principles)** **Positive-sum utility** ( collaboration must be positive-sum) ｜ **Tax anchoring** ( utility anchors to tax, not to price or profit) ｜ **Zero tolerance for negative space** ｜ **Auditable and traceable** ( no attestation, no execution).

---

## 2. Ownership registration ( phase-one segment · under scenario constraint)

**Article 5 (Entry)** **Anything with a form of expression may be registered** ( inheriting the old instrument's open entry).

**Article 6 (Four legal domains)** form of expression → **copyright**; invention → **patent law**; digital structuring → **data law**; mark → **trademark law**.

**Article 7 (Requirements)** **Scenario of attribution** ＋ **provenance lineage of generation**.

**Article 8 (Boundary)** Phase one covers only **registration / change / cancellation / query**; **transfer / license** ( disposal of rights) **is not in phase one**.

**Article 9 (Mode of rights confirmation · self-sufficient)** Rights are confirmed **by a self-sufficient registration system**; rights-confirmation registration is **a precondition of `L2` authorization**.

---

## 3. Authorization registration and the authorization instrument

**Article 10 (Split)** **Ownership registration** ( who owns it) / **authorization registration** ( who may use it, how); the two **are separate instruments** ( neither is complete without the other; each is the other's premise).

**Article 11 (Four requirements)** **Scenario constraint** ( mandatory) ｜ **five-tier asset form** ｜ **full composition authorized** ｜ **legal-entity signature**.

**Article 12 (Signature forms)** **Electronic signature** and **authorization code** ( both must be presented by the principal; **no agent may hold, fill in, or sign**); the form type is logged to `NCA`, the four requirements are unchanged.

**Article 13 (Interpretant = the authorization instrument)** The interpretant = **the authorization-registration instrument**; **no invocation without authorization**; **configuration without authorization = infringement** ( the only exception is **sandbox drills** · **leaving the sandbox requires authorization**).

**Article 14 (Own assets also need an instrument)** **Own assets also require an authorization instrument** ( not exempt because ownership rests with oneself).

**Article 15 (Multi-tier)** Multi-tier authorization **requires an instrument and a signature at every tier**; the tier ceiling **is reserved to the founder**.

**Article 16 (Operational layer)** The authorization-management panel **has five operations** ( pre-receipt / real-time authorization / additional authorization / license change / multi-tier authorization); templates **standard form + custom form**; the panel's institutional hard constraints follow the registered design instrument ( `TDCA-DESIGN-AUTH-PANEL-001`).

---

## 4. Publicity and public notice

**Article 17 (Public face)** Ownership instruments and authorization instruments **are searchable network-wide** ( **four fields**: ownership information / authorization information / authorization status / how to obtain); "how to obtain" **does not equal authorization already obtained**.

**Article 18 (Publication of terms)** **Initial terms must be public** ( otherwise whether configuration is permissible cannot be computed); publication of **negotiated terms** **requires both parties' consistent sign-off**; publication **may not be withdrawn**; negotiation granularity is customizable.

**Article 19 (Four non-disclosure items)** **internal identifiers** ｜ **credentials and keys** ｜ **sensitive natural-person information** ｜ **negative-space vocabulary**.

**Article 20 (Offer configuration network)** Authorizer's offer ( unilaterally sets initial terms · **must be public**) → requester's offer ( unilaterally sets demand-side initial terms · **must be public**) → negotiation ( **bidirectional**; publication of negotiated terms requires **both parties' consistent sign-off**) → conclusion ( an authorization instrument is generated · **all four requirements present**) → **a many-to-many network**.

---

## 5. Market operation ( inherited from the old general specification, chapter 1, six items · aligned item by item)

| Item | Matter | This draft ( after rewriting) | Pending |
|---|---|---|---|
| `1` | Market admission | Admission presupposes **contracting ＋ ownership / authorization registration** ( inheriting the old instrument's "four-end subject admission" sense · the four-end classification names **follow registered terminology**) | admission threshold values |
| `2` | Trading rules | Trading **is limited to configuration rights** ( ownership does not circulate); matching dual-track ( inherited) | matching details |
| `3` | Pricing and valuation | Pricing **anchors to positive-sum utility and tax anchoring** ( not to price or profit); fees transcribed from the old instrument and marked pending review | **rates reserved to the founder** |
| `4` | Settlement and distribution | Settlement **in `SIMULATED` sandbox state** ( phase one); distribution per registered rules ( `Shapley` position per registered instruments · this side does not decide algorithms) | parameter values |
| `5` | Information disclosure | Inherits §4 ( public face ＋ four fields ＋ four non-disclosure items) | — |
| `6` | Dispute and exit | Disputes **are reconciled only by `TDCA`** ( recording / attestation / registration; no adjudication, no disposal, no debt recovery on behalf); the responsible entity **is the law-enforcement authority**; exit and de-listing inherit the old instrument | the wording "adjudication" · reserved to the founder |

---

## 6. Interface with registered institutions ( point by point)

| # | Registered instrument | Interface point |
|---|---|---|
| `1` | `TDCA-STD-SRIGHT-001` ( scenario configuration-right invocation interface specification) | This draft sets the **institutional face**; the **invocation implementation face** follows that instrument ( the human-readable version is the semantic authority · no machine-readable reverse change of semantics) |
| `2` | configuration-right usage and effect-path basis (drafting basis) | Configuration-right usage follows "**a scenario may be formally expressed as a function**"; the effect path follows "**each governs its own face**" |
| `3` | `TDCA-STD-METAFUNC-ACCORD-001` ( `REV2`) | The **relation face** ( metafunction ⟷ interpretant) follows that instrument; role = **reconciliation**; terms **agreed at contracting** ( no unilateral post-hoc addition) |
| `4` | "minimum configuration unit = scenario" (terminology basis) | The **minimum configuration unit = scenario** ( internal elements do not participate in configuration directly) |
| `5` | positive-sum discrimination and handling basis (drafting basis) | Positive-sum discrimination = **discriminative power**; handling **adjust configuration weight · adjust presence** |
| `6` | Registered `MOU` ontology position ＋ `RULING-PHASE1-BUILD-PROPOSAL-001` ( five tiers) | Anchoring = **floor, not ceiling**; the five-tier formulation **follows the registered wording** |
| `7` | `TDCA-REGISTER-CONTRACT-001` ( contracting triad) | The root of admission; **human signature right** ( no agent may exercise it on behalf) |

---

## 7. External dependencies and migration slots ( six items · per the founder's position)

| # | External item | Current self-sufficient form | Migration slot | Migration condition |
|---|---|---|---|---|
| `1` | external rights-confirmation body ( statutory trading centre) | registration system | confirmation act moves out | external connection ( timing reserved to the founder) |
| `2` | four-party representative joint signature | legal-entity signature ＋ both parties' consistent sign-off | add a joint-signature track ( parallel · not a substitute) | external representative entities connected |
| `3` | real digital-RMB ledger | `SIMULATED` sandbox | connect the real channel | channel and compliance ready |
| `4` | physical node anchoring | carrier-readiness discipline ( ready but without `transport` may not be passed off as executed) | physical anchoring live test | physical and test environments connected |
| `5` | judicial / law-enforcement disposal | reconciliation only ( recording / attestation / registration) | no migration needed ( already so in registered rules) | interface retained as evidence |
| `6` | market invocation protocol and scheduling tax | interface layer `DRAFT` | interface layer upgraded | pending sign-off |

---

## 8. Supplementary provisions

**1 (Dual-version obligation)** This specification is **specification-level · hard constraint** ⟹ **dual version required** ( Chinese / English / machine-readable triad); manuals / guidelines / guide-type annexes **are human-readable only**.
**2 (Effectiveness)** This instrument **is in force (`V1.0-FROZEN` · 2026-10-03)**; the effect scope is Phase-1 internal operation, while public launch requires a separate statement; numeric items are determined separately as registered.
**3 (Style)** The human-readable version is the **semantic authority**; the machine-readable version may not reverse-change semantics; the English translation is provided as of this instrument.

---

## 9. Annex list ( the remaining class-`A` **12** instruments as annexes · per the recommended position)

| # | Annex | Position ( under this draft) |
|---|---|---|
| `1` | node access standard ( draft `V0.2`) | technical annex ( physical anchoring as a migration slot) |
| `2` | invocation-constraint intensity selector ( manual `V1.0`) | manual level ( **human-readable only**) · parameters pending |
| `3` | `CLARIFY-001` ( three-layer distinction) | conceptual annex ( same lineage as the integrated draft) |
| `4` | `CLARIFY-002` ( boundary and economic realization) | conceptual annex |
| `5` | `CLARIFY-INTEGRATED-001` ( complete institutional definition · integrated draft) | conceptual annex ( **later issuer within the family**) |
| `6` | `FUNC-FORMAL-001` ( `Ψ` calculus) | **mathematical annex** ⟹ this side does not draft / review / judge it ( conditional · citations must carry sources) |
| `7` | `MOU-PRECISION-001` | calculation family ( **superseded by the final confirmation** · archived only) |
| `8` | `MOU-FINAL-001` ( final confirmation) | calculation family ( conclusive citable · values pending) |
| `9` | `MOU-SCENE-BOUNDARY-001` | scenario-boundary family ( superseded · archived only) |
| `10` | `MOU-SCENE-FINAL-001` ( final confirmation) | scenario-boundary family ( digital RMB `SIMULATED` · migration slot) |
| `11` | `CORE-PRINCIPLE-001` | principle instrument ( same lineage as the principle articles) |
| `12` | `CORE-PRINCIPLE-PRECISION-001` ( precision finalization) | principle instrument ( **later issuer within the family**) |


---

## 10. Reserved to the founder ( one item per line · this side does not decide)

| # | Item |
|---|---|
| `1` | **fee and service-charge values** ( the old instrument reads "a certain proportion of the transaction amount · periodically reviewed and published 30 days in advance" ⟹ the proportion and the reviewing body are reserved to the founder) |
| `2` | **confirmation of the five-tier clause-by-clause reconciliation** ( whether it maps one-to-one onto the registered five tiers) |
| `3` | **the wording of "dispute and adjudication"** ( whether to keep the word "adjudication" · how to handle the tension with the registered "reconciliation only") |
| `4` | **the tier ceiling for multi-tier authorization** and **per-tier requirements** ( not recorded in the old instrument) |
| `5` | **admission threshold values** ( no concrete threshold recorded in the old instrument) |

---

## 11. Boundaries and self-check

1. This instrument is a **specification** (`V1.0-FROZEN` · in force · not a judicial ruling); it **amends** no desktop instrument, registered instrument or counterparty-side instrument ( **append-only**); changes go through `PR`.
2. **Zero external exposure**; this side has **not pushed, not merged, not deployed, not logged in, not handed over**; **no credential values and no personal names**; **time zone +08**.
3. Does not decide thresholds / weights / bars / scale / signing authority / **institution-layer semantics** on the founder's behalf; **no mathematical content** ( the mathematical layer is pointed to as an annex only), **no legal opinion**, **no legal determination**.
4. **Faithful registration**: "rewritten from the class-`A` master text" is done ( inheriting the old three-chapter `22`-article style · aligned clause by clause with the reconciliation instrument); **values from the old instrument** are transcribed throughout and marked "pending founder review" ( this side has not substituted new values); this draft **takes effect only after the four steps ＋ sign-off**.

---

---

**Version** V1.0-FROZEN (in force 2026-10-03; scope: Phase-1 internal operation; public launch requires a separate statement)
