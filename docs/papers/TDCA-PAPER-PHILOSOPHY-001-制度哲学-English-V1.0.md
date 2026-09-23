# TDCA Institutional Philosophy: From the Self-Consistency Paradox to External Anchoring

——On the Ontological Foundations of Institutions in the Agent-Native Era

> **Document ID**: **TDCA-PAPER-PHILOSOPHY-001** ｜ **Version**: **V1.0 (English)** ｜ **Date**: **2026-09-23** (+08)
> **Nature**: TDCA foundational paper (institutional philosophy) ｜ **Positioning**: ⭐ a TDCA foundational paper — the **sister paper** of *TDCA Engineering Philosophy: Isomorphic Realization from Flow to Function* (the former answers "why institutions are designed this way", the latter "how institutions are realized")
> **Status**: **Public version V1.0** (⚠️ may be elevated after the institutional re-review gate signs off)
> **Discipline**: ⭐ **three-state principle** (`proved` / `refuted` / `conditional` are all legitimate final states); ⛔ **no claim of "absolute security"**; ⭐ **simulated state explicitly labelled** (`SIMULATED`)
> **Single source of truth**: ⭐ formal status is governed by the repository files `CLAIMS-MATRIX.md` and `OPEN-PROBLEMS.md`
> This is the public version; the text contains no internal serial numbers or internal identifiers.

---

**Abstract**

This paper poses and answers a fundamental paradox facing institutional design in the agent-native era: a system that is not self-consistent can hardly be recognized externally as stable and reliable, yet a self-consistent system depends on external certification, which itself lies outside the system. Using TDCA (Trusted Digital Collaboration Architecture) as the instance, the paper argues that the resolution lies not in the pursuit of absolute self-consistency but in a **three-fold structure**: an internally verifiable closed loop, external three-fold anchoring, and the human signature right. It further argues that the ontological divide between the institutional-state twin and the digital twin is not a matter of technical layers but of ontology — the former mirrors rules and institutional states, the latter mirrors physical states; and that the minimal configuration unit of an institution is the **scene quantum**, not the project. The paper then sets out the yin-yang structure of institutional evolution: problems and standards are co-originating, and standards are discovered through interaction with errors and consolidated through a case mechanism rather than designed a priori. Finally, it establishes the ontological position of the execution entity: AI is not a subject but an executor of functions; what institutions govern are functions and cognitive assets, not agent identities.

**Keywords**: institutional philosophy; external anchoring; self-consistency paradox; institutional-state twin; scene quantum; cognitive asset; judging by traces, not by minds

---

## I. Introduction: A Philosophical Paradox

Every institutional system faces a fundamental paradox:

> A system that is not self-consistent cannot be recognized externally as stable and reliable.
> But a self-consistent system depends on external certification, and external certification itself lies outside the system.

In mathematics this corresponds to Gödel's incompleteness theorem: a sufficiently strong consistent system cannot prove its own consistency. In physics it corresponds to the observer problem: any observation depends on an observational frame, and the frame itself cannot be verified by the same observation. In institutional theory it corresponds to the question "who signs the meta-rule": institutions need authority, authority needs institutions, and the two are circularly dependent.

Taking TDCA as the instance, this paper argues the resolution.

**Core thesis: the stability of an institution does not come from absolute self-consistency, but from the dynamic balance of a three-fold structure — an internally verifiable closed loop, external three-fold anchoring, and the human signature right.**

It should be stated at the outset that every philosophical proposition in this paper has a corresponding **machine-verifiable carrier** in the TDCA system (⚠️ its **current status** — `proved` / `conditional` / `SIMULATED` — is governed by `CLAIMS-MATRIX.md`; this paper ⛔ does not adjudicate that status). The paper is not a philosophical reverie about institutions, but a philosophical reflection on an institutional system that is partly formalized and partly engineered. The function of philosophy is to reveal structure; the existence of engineering makes that structure testable.

## II. Structural Analysis of the Self-Consistency Paradox

### 2.1 The Predicament of a Purely Self-Consistent System

A system that depends entirely on internal logic faces three predicaments:

**Predicament 1: it cannot prove its own consistency.** Gödel showed that a sufficiently strong formal system cannot prove its own consistency. The same holds for institutions: every institution rests on certain unproved axioms or untested premises.

**Predicament 2: it cannot connect to reality.** A purely self-consistent system may be an elegant mathematical structure or a closed doctrine. It can prove itself, but it cannot prove its relation to reality.

**Predicament 3: it cannot handle evolution.** A purely self-consistent system can evolve only within its own space and cannot respond to changes in the outside world. When the outside world changes fundamentally, such a system ossifies or collapses.

### 2.2 The Predicament of a Purely Externally-Anchored System

A system that depends entirely on external authority faces three predicaments of its own:

**Predicament 1: it cannot establish a stable core.** When external authority changes, the system changes with it; there is no independent logical structure to support internal consistency.

**Predicament 2: it cannot handle conflicting authorities.** When multiple external authorities issue different certifications, the system cannot judge internally which is more credible.

**Predicament 3: it cannot evolve.** External authorities themselves evolve; a system that merely follows them cannot form its own cumulative structure.

### 2.3 The Resolution: Dynamic Balance of a Three-Fold Structure

TDCA's resolution is to establish the dynamic balance of a three-fold structure:

**First fold: an internally verifiable closed loop.**
The sixteen constitutional hard constraints (C₁₆), functional formalization, the nested cognitive asset (NCA) attestation chain, the assertion-anchor state machine, and Shapley allocation together constitute TDCA's internal logical loop. They do not claim absolute self-consistency, but they do claim to be formally verifiable, machine-executable, and auditable.

**Second fold: external three-fold anchoring.**
External anchoring lies outside the TDCA system but provides it with verification baselines from outside. It consists of three mutually independent layers, none dispensable:

- **Legal anchoring**: the administrative and judicial dual force of the copyright chain and the Tianping chain, providing an out-of-system adjudication channel for rights confirmation;
- **Economic anchoring**: the legal-tender nature of the digital renminbi, the fiscal fact of the taxation system, and the tax anchoring of the minimum observable utility (MOU) — providing an unforgeable hard floor for utility claims;
- **Physical anchoring**: a trust root composed of SRAM PUF, national-cryptography secure element (SE), TDID hardware identity, and physical fuse wires — providing a physical carrier for "machines attesting their own traces": the storage of verification public keys, the execution of fusing, and the non-persistence of key material, all terminating at the physical boundary of the chip package.

The institutional significance of the physical anchoring layer deserves separate treatment: without it, the **verifiability itself** of the internally verifiable closed loop hangs in the air — verification requires public keys, and the authority of public keys requires anchoring; fusing requires an executor, and if the executor can be rewritten by software, the fuse itself becomes the target of attack. Physical anchoring answers the question: on what basis does a machine attest its own traces? The trust root terminates at silicon, and institutions thereby obtain a final baseline against software-layer self-reference attacks.

Physical anchoring follows a **layered principle**, configured by the value and risk of the protected object rather than as a blanket rule: high-value scenes (institutionally anchored devices, metering infrastructure, fuse execution points) take the full configuration of secure elements, physically unclonable material and physical fuse wires; medium scenes take hardware identity plus secure-element signatures; ordinary scenes admit software-level certificate chains as a downgraded trust root — reduced trust strength, extended usability. There is one hard boundary to the layering: **the trust-root tier is bound to the scene's confidentiality level, and a high-confidentiality scene does not accept a lower-tier trust root**; verification failure means denial of admission. Layering is an institutional trade-off between cost and security, not a compromise of the trust standard.

**Third fold: the human signature right.**
The human signature right cannot be bypassed — this is not a formal clause in TDCA but a structural constraint — for only a human can bear the answer to "who am I", and only a human can be responsible for the final judgment. AI is an executor of functions, has no ontology, and cannot bear ultimate responsibility.

If any one of the three is missing, the institution drifts; with all three present, the institution can maintain an iterable stability between self-consistency and external recognition.

### 2.4 Institutional Collateral of the Three-Fold Structure: From Philosophical Proposition to Machine Verification

The core thesis of this section is not a design claim in TDCA but has already been realized as institutional collateral. TDCA's self-reflexive compounding principle (an internal institutional document) addressed self-reference long ago: the framework's own credibility claim is self-referential, and to prevent self-certification loops that claim is **collateralized to three layers — machine-readable, hash-verifiable, and externally auditable**. The three-fold structure of this section is precisely the philosophical expression of that collateral:

| Philosophical structure | Machine-verifiable carrier | Repository location | ⚠️ Status (governed by `CLAIMS-MATRIX.md`) |
|---|---|---|---|
| Internally verifiable closed loop | Main theorem (institutional credibility across the three spaces): adjudicated propositions in the positive space, fuse completeness in the negative space, hard-data adjudication in the sandbox — their conjunction constitutes completeness and soundness | formal proofs repository / `CLAIMS-MATRIX` | ⚠️ delivered in parts; per-item status in the matrix |
| External three-fold anchoring | The MOU tax-anchoring principle (a hard floor for the minimum observable utility), the uniqueness principle of digital-renminbi smart contracts (hard constraint at the legal-currency layer), the notification machine protocol package V1.0 (**FROZEN**, physical trust root) | notification machine engineering / economic operation layer | ⚠️ anchoring interfaces are currently `SIMULATED` |
| Human signature right | Signing authority narrows link by link along the chain: the closer to the positive space, the fewer the signing nodes and the more concentrated the responsibility; stage 3 of the cognitive production line (think-tank project initiation) is the first landing of the human signature right | `docs/identity` / governance process | ✅ landed |

The reverse relation deserves emphasis: a Gödelian argument can only tell us that self-certification is impossible; TDCA's collateral structure answers what to do given that impossibility — **split the credibility claim into three heterogeneous carriers so that the failure of any one layer does not collapse the whole**. This is not an evasion of the incompleteness theorem but an engineering response to it.

## III. Institutional-State Twin: The Ontological Divide from the Digital Twin

### 3.1 The Limits of the Digital Twin

The digital twin is a mirror at the object layer. It answers "what is this device's temperature now" or "what is this line's current yield". It moves observable physical states into the digital world, but does not touch ownership, rules, allocation, or responsibility.

A digital twin can only be partial, because it can only cover physical states capturable by sensors and cannot cover the operational logic at the institutional layer.

### 3.2 The Globality of the Institutional-State Twin

The institutional-state twin mirrors institutional logic itself — how ownership is defined, how use rights are configured, who may schedule what, how value is measured, how violations are fused, how disputes are remedied.

It is not a static rule base; it is itself a dynamic state system. What the institutional-state twin mirrors includes: the activity states of scene quanta, the current attribution of configuration rights, the integrity of the NCA chain tail, the accumulated value of MOU anchoring, the lifecycles of assertion anchors, and the **institutional admission state** of execution-entity instances (⚠️ not "identity state" — see §6.2).

An institution is not a static text; an institution is a dynamically running state machine.

### 3.3 Coupling the Two Data Dimensions

The physical-state twin and the institutional-state twin are two independent data dimensions:

- Physical dimension: time, space, magnitude, physical quantity.
- Institutional dimension: time, scene, subject, right, state, utility, responsibility.

The two couple through the scene quantum: physical states enter the scene quantum via physical anchoring (sensors, PUF, metering chips), institutional states enter the scene quantum likewise, the scene quantum performs rule adjudication and state transition internally, and the results are written back into both twin dimensions.

Complete topology = physical-state twin + institutional-state twin + the scene-quantum coupling layer.

## IV. Scene Quantum: The Minimal Configuration Unit

### 4.1 The Limits of Project-Based Configuration

Traditional project-based configuration takes the "task" as its boundary and cuts resources and rules into pieces. Projects cannot collaborate, because their data structures, permission models, and audit conventions differ.

### 4.2 The Globality of Scene-Based Configuration

The scene quantum is the minimal configuration unit. A scene quantum defines a complete collaboration boundary: who participates, which tools are available, what permission scope applies, what negative space exists, what utility function governs, and what audit requirements apply.

A new project does not need to be configured from scratch; it only needs to declare which scene quantum it belongs to, or create a new one, and it then automatically inherits that scene's rules, permissions, audit and allocation mechanisms.

Scene-based configuration makes resources and rules reusable, inheritable, and composable.

### 4.3 Why the Distinction Matters

First, the scene is the coupling point between the digital twin and the institutional-state twin. Second, the scene makes cross-project collaboration possible. Third, the scene makes configuration rights genuinely schedulable — the minimal trading unit of a configuration right is a single scene utility function, the universe of institutional objects is well defined by the scene-type constructors, and the completeness branch of the main theorem can therefore be stated.

Every project should be an instance of a scene quantum, not the other way around.

## V. Institutional Evolution: The Yin-Yang Structure of Problems and Standards

### 5.1 The Unity of Errors and Standards

Traditional methodology assumes that methods are used to solve problems and problems are what methods eliminate: the two are opposed.

Another structure is possible: problems themselves are the raw material of standards.

- Without errors, there is no boundary of a standard.
- Without a standard, nothing can be judged an error.
- The two are mutually conditioning.

Standards define errors, and errors validate standards. A standard is calibrated in the process of identifying errors, and errors are classified under the judgment of the standard.

### 5.2 The Way of Yin and Yang: Mutual Rooting, Mutual Use, Waxing and Waning, Transformation

- **Mutual rooting**: without errors there is no standard; without a standard there is no error.
- **Mutual use**: a standard verifies itself by identifying errors; errors push the standard to iterate by exposing its boundary.
- **Waxing and waning**: as the standard expands, errors are compressed to a new boundary; as errors are eliminated, the standard ossifies.
- **Transformation**: yesterday's error may become the seed of a new standard; today's standard may become the source of a new error.

The yin-yang structure is not a metaphor in TDCA but an already running mechanism. Red-team breaches produce cases; cases are consolidated into a reproducible case library through NCA attestation; the case library produces institutional increments through the institutional re-review gate; increments are versioned through the online-upgrade (OTA) mechanism — this is the institutional channel by which "yesterday's error becomes the seed of a new standard", and the dynamic explanation of the "living constitution" (which supports incremental institutional upgrades while the negative space may only be tightened, never loosened). Each time a standard solidifies, the red team's attack surface shifts — and so the waxing and waning continue.

One apparent tension must be handled here: the living constitution permits incremental upgrades, while the negative-space standard may only be tightened. If a negative-space item turns out to be a misjudgment, what then? The answer is **reclassification, not deletion**: the misjudged item does not disappear from the institution (that would be loosening); it **migrates** from the negative-space list to scene constraints or positive-space rules, with the migration requiring human sign-off and leaving a case record. The baseline only grows and never shrinks, but items may change position — a correction of misjudgment is recorded institutionally as the evolution of the standard, not as a retreat of the baseline.

### 5.3 Red-Team Breaches: The Best Method for Identifying Exceptions

Before AI red teams, the grey zone between overreach and innovation depended on the subjective judgment of a few experts — expensive and irreproducible.

Now: AI red teams attack deliberately, and the breach point is the boundary line.

- Where the red team can breach is where the boundary of the institution lies.
- What it cannot breach is what the institution already covers.
- Every breach leaves a case through NCA attestation, forming a reproducible, auditable, iterable mechanism for identifying exceptions.

AI plays the red team; humans adjudicate. The human signature right appears here as the axis of yin and yang: the two poles interact to produce evolution, but the authority to decide the direction of evolution is in neither pole.

## VI. Judging by Traces, Not by Minds: The Ontological Position of Execution Entities

### 6.1 AI Is Not a Subject but an Executor of Functions

The fundamental error of mainstream AI governance is to treat AI as a "non-human identity" that must be issued an identity, assigned a role, and granted permissions like a human employee.

But AI is not a subject. It has no institutionally continuous responsible subject: its memory is a technical carrier rather than a bearer of responsibility, and its "identity" is essentially an instantiation parameter of a function, not a subject.

Assigning an identity to an ontology that does not exist is an ontological error.

### 6.2 TDCA's Alternative: No Identities, Only Anchored Traces

- Do not issue identities to AI; issue an NCA attestation for every call AI makes.
- Do not govern AI's roles; govern AI's scene boundaries.
- Do not track AI's identity lifecycle; track AI's context and utility.

One precise distinction is required here, or it will cause misreading at the engineering layer: **TDCA does not track the identity lifecycle of an execution entity** (who it is, what it is called, how long it lives), **but it does manage the entity's institutional admission state** (unregistered, registered, certified, active, degraded, suspended, fused) — the latter is the carrier state of functional admission, serving the question "has this call been compiled and verified", not a household registration of a subject. An institution attends to an execution entity only because it is the carrier of functions and traces; once a carrier no longer carries legitimate functions, its institutional state terminates, and what becomes of the carrier itself is not an institutional question.

**The object of rights confirmation in call attestation is the cognitive asset** — an expression recognized by the institution, measurable and allocable. TDCA's governance objects are thereby fully delimited: functions (expression boundaries), cognitive assets (objects of rights confirmation), and scene utility (basis of allocation). Execution entities are not among them.

Rights confirmation takes signature as its condition of effect: a human signature, or an institutionally authorized proxy signature (automatic signing within an already-contracted scene is of this kind). Generated content that has not been signed is merely a **candidate asset** — it may be recorded, reviewed and traced, but produces no confirmation effect and takes no part in allocation. A candidate asset is the raw material of the institution, not its object; the signature is the stroke that converts raw material into object.

Judging by traces, not by minds. Do not interrogate AI's "mind"; verify only AI's "traces".

### 6.3 The Structural Necessity of the Human Signature Right

Humans have identity, responsibility, the right to sign, and final adjudication. AI has no identity, only traces; no role, only scenes; no responsibility, only boundaries.

The human signature right cannot be bypassed precisely because only a human has the "I" that can bear responsibility.

## VII. Duality with the Engineering Philosophy (⭐ added in V1.3)

This paper (institutional philosophy) and *TDCA Engineering Philosophy* form a **duality**: this paper answers "why institutions are designed this way", the other "how institutions are realized as runnable machine behaviour". The two are structurally interlocked as follows:

| # | ⭐ Institutional side (this paper) | ⭐ Engineering side (engineering philosophy) | ⭐ Interlock |
|---:|---|---|---|
| 1 | **Internally verifiable closed loop** of the three-fold structure | The three compiled execution-core components (negative-space enforcement, attestation, fusing) plus the daemon | ⭐ institutional "verifiability" = engineering "deterministic execution in the fast system" |
| 2 | **Legal anchoring** of external three-fold anchoring | Rights-confirmation interface and judicial access channel | exit for rights-confirmation effect |
| 3 | **Economic anchoring** | Utility metering module and tax-anchoring interface (`SIMULATED`, explicitly labelled) | ⭐ simulated labelling = the honest engineering expression of economic anchoring |
| 4 | **Physical anchoring** (layered, bound to confidentiality) | The notification machine (protected storage partition, secure-element signatures, non-persistent PUF keys, dual physical/institutional fusing) | ⭐ this paper's "layered principle" ↔ the other's "**the trust chain terminates at the chip package**" — one is institutional layering, the other an engineering terminus, **complementary and non-overlapping** |
| 5 | Human signature right | Slow-system sign-off column + signing authority narrowed link by link | legality division of labour |
| 6 | Institutional-state twin (mirroring rules and institutional states) | Data as flow (judged, metered, recorded on every passage through a scene) | ⭐ twin dimension ↔ flow capture |
| 7 | Scene quantum (minimal configuration unit) | Scene function (five-domain signature: input / output / constraint / permission / audit) | ⭐ one thing, two expressions |
| 8 | Judging by traces, not by minds (admission state, not identity) | Execution entities read functions (seven-state admission state machine) | ⭐ ontological discipline ↔ engineering realization |
| 9 | Yin-yang structure (case library + living-constitution OTA) | Evolution synchronization (fail-closed version-alignment gate) | ⭐ institutional evolution ↔ engineering synchronization |
| 10 | Configuration right (the third pole) | Configuration-right scheduling (an executable function) | ⭐ institutional definition ↔ runtime behaviour |

⭐ **The meaning of the duality**: taken together, the two papers constitute a complete system of "executable institutions" — the institutional side provides the **structural grounds**, the engineering side the **operational counterparts**; and the formal follow-up propositions jointly implied by both, which the proof program's seven propositions do not yet cover (trust-root resilience, confidentiality-tiered trust roots, the admission state machine, fail-closed version alignment, dual-anchor consistency, the negative-space migration invariant, and the existence of fast–slow interfaces), have been extracted separately by our side (see the internal review document). ⛔ This paper does not adjudicate their formal content.

## VIII. Conclusion

This paper has argued three core propositions of TDCA's institutional philosophy:

**Proposition 1: the resolution of the self-consistency paradox lies not in absolute self-consistency but in the dynamic balance of a three-fold structure.** An internally verifiable closed loop + external three-fold anchoring (legal, economic, physical) + the human signature right: if any one is missing, the institution drifts. This structure has been realized in TDCA as machine-verifiable institutional collateral, an engineering response to the Gödelian predicament.

**Proposition 2: the institutional-state twin and the digital twin are divided by ontology, not by technical layer.** The institutional-state twin mirrors rules and institutional states; the digital twin mirrors physical states. They couple through the scene quantum, which is the sole coupling point of the two twins and the minimal trading unit of configuration rights.

**Proposition 3: institutional evolution is the yin-yang interaction of problems and standards.** Standards are defined in identifying errors, and errors are discovered under the judgment of standards. The red team is one pole of yin and yang, the human signature right is the axis, and the case library together with living-constitution OTA is the institutional channel of that interaction.

Final positioning: an institution does not pursue the perfection of self-consistency, but maintains an iterable balance between self-consistency and external recognition. Whether the universe is self-consistent is conferred by human cognition; and human cognition itself covers only a small part of the universe. The stability of an institution comes not from a claim of absolute self-consistency, but from the presence of three structural conditions — and in TDCA these three conditions are not a claim but a fact that can be verified by opening the repository item by item.

## References

[1] TDCA Research Group. Function Whitepaper: A Formal Theory of Institutional Utility Configuration. V2.0-FROZEN, 2026.
[2] TDCA Research Group. Judging by Traces, Not by Minds: A Trustworthy Multi-Agent Collaboration Protocol. V1.0-FROZEN, 2026.
[3] TDCA Research Group. Functional Large Models: A Second Paradigm Beyond Parametric Large Models. V1.1-FROZEN, 2026.
[4] TDCA Research Group. Development, Not White-Boxing: The Epistemic Positioning of Thought Protocols. Released, 2026.
[5] TDCA Research Group. Assertion Anchors and Hybrid Juridical Topology. V1.4-PUBLISH, 2026.
[6] Gödel K. Über formal unentscheidbare Sätze der Principia Mathematica und verwandter Systeme I. Monatshefte für Mathematik und Physik, 38:173–198, 1931.
[7] TDCA Research Group. The Self-Reflexive Compounding Principle and the Structure of Institutional Collateral. 2026.
[8] TDCA Research Group. Notification Machine Protocol Package (system specification / firmware metadata specification / compliance review report). V1.0 FROZEN, 2026-08-11.

---

**Document status**: **V1.0 (English)**. Under TDCA discipline, the mechanisms described here are **design-state and philosophical propositions**, not claims about the running system; all formal status is governed by the repository files `CLAIMS-MATRIX.md` and `OPEN-PROBLEMS.md` as the **single source of truth**.

## Revision History

| # | Revision | Nature |
|---|---|---|
| 1 | "Cognitive asset" enters abstract and keywords; §6.2 adds the definition of the object of rights confirmation | substantive: the first-order object acquires a name at the philosophical layer |
| 2 | External anchoring expanded from two layers to three (legal / economic / physical); physical anchoring enters the body | substantive: closes a substantive gap |
| 3 | §2.4 added: explicit mapping table from the three-fold structure to the three-layer collateral | precision: philosophical propositions attached to machine-verifiable carriers |
| 4 | §5.2/§5.3: yin-yang structure = case library + living-constitution OTA | precision: metaphor lands as institution |
| 5 | §6.1 institutional-layer phrasing; §6.2 adds the precise distinction between identity lifecycle and institutional admission state | substantive: removes an apparent conflict with the engineering layer |
| 6 | Removed a reference with no purchase on the text; added refs [7] and [8] | substantive: all references interlock |
| 7 | Internal codes throughout the body converted to plain names | readability |
| 8 | Physical-anchoring layer adds the layered implementation note (cost–security tiering, hard boundary at confidentiality binding) | strengthening: answers cost and availability objections |
| 9 | §5.2 adds the reclassification mechanism for negative-space misjudgment (migration, not deletion; human sign-off leaves a case) | strengthening: dissolves the apparent tension between the living constitution and "tighten only" |
| 10 | §6.2 adds the boundary of rights confirmation (signature takes effect; unsigned content is a candidate asset) | strengthening: condition of effect and candidate-asset distinction |
| 11 | Compliance pass: standard document head and discipline statements (three-state principle, no absolute security, simulated labelling, single source of truth) | compliance |
| 12 | Sister-paper cross-reference added (head and new §VII): duality with the engineering philosophy | compliance |
| 13 | Version chain normalized to V1.0 (English) | compliance |
| 14 | §2.4 carrier table gains a per-item "Status" column (⚠️ governed by `CLAIMS-MATRIX.md`); "machine-verifiable carrier" uniformly status-qualified to avoid being read as "proved" | red-line compliance |
| 15 | First-occurrence terms spelled out in full (nested cognitive asset, NCA; minimum observable utility, MOU; secure element, SE) | terminology consistency |
| 16 | ⭐ §VII "Duality with the Engineering Philosophy" added (ten-item interlock table) | structural strengthening |

> ⚠️ The present edition is the **public (English) version**: the document head is the public head, terms follow the five rulings of the terminology decision, and references are given as plain titles without internal document numbers; ⛔ **no philosophical proposition has been altered in substance**.
