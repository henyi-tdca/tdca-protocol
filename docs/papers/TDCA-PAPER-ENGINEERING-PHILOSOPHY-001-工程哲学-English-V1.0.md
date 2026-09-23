# TDCA Engineering Philosophy: Isomorphic Realization from Flow to Function

——On the Structural Correspondence between Institutions and Technology

> **Document ID**: **TDCA-PAPER-ENGINEERING-PHILOSOPHY-001** ｜ **Version**: **V1.0 (English)** ｜ **Date**: **2026-09-23** (+08)
> **Nature**: TDCA foundational paper (engineering philosophy) ｜ **Positioning**: ⭐ a TDCA foundational paper — the **sister paper** of *TDCA Institutional Philosophy: From the Self-Consistency Paradox to External Anchoring* (the latter answers "why institutions are designed this way", this paper "how institutions are realized")
> **Status**: **Public version V1.0** (⚠️ may be elevated after the institutional re-review gate signs off)
> **Discipline**: ⭐ **three-state principle** (`proved` / `refuted` / `conditional` are all legitimate final states); ⛔ **no claim of "absolute security"**; ⭐ **simulated state explicitly labelled** (`SIMULATED`); ⛔ **no claim of "proved"**
> **Single source of truth**: ⭐ formal status is governed by the repository files `CLAIMS-MATRIX.md` and `OPEN-PROBLEMS.md`
> This is the public version; the text contains no internal serial numbers or internal identifiers.

---

**Abstract**

This paper is the sister paper of *TDCA Institutional Philosophy: From the Self-Consistency Paradox to External Anchoring*: the institutional philosophy answers "why institutions are designed this way", the engineering philosophy answers "how institutions are realized as runnable systems". The paper argues that TDCA's engineering structure is not a "translation" of institutional logic but an "isomorphism" of it — every layer of the institution has a runnable counterpart on the engineering side. Across six layers — anchor alignment, data as flow, scene as function, execution entities reading functions, the fast/slow system split, and configuration-right scheduling — the paper sets out the core propositions of TDCA's engineering philosophy; it argues the engineering forms of the three-fold anchoring (legal, economic, physical); and it gives four criteria for institutional–technical isomorphism: structural correspondence, executable verifiability, traceable failure, and synchronized evolution — each carrying its **registered carriers** in the repository (⚠️ their status is governed by `CLAIMS-MATRIX.md`). The core proposition is that engineering philosophy is not "how to write code" but "how institutional logic is realized as runnable, auditable, fusable machine behaviour".

**Keywords**: engineering philosophy; institutional isomorphism; anchor alignment; data as flow; scene as function; fast and slow systems; physical trust root; executable institutions

---

## I. Introduction: Why Engineering Needs Philosophy

TDCA's institutional philosophy has answered "why institutions are designed this way". But no matter how rigorously an institution is designed, if it cannot be realized in engineering it remains a thought experiment.

The relation between institution and engineering is not the linear "design the institution first, then implement the engineering" but an isomorphic relation — every structure of the institution has a runnable counterpart on the engineering side, and every mechanism of the implementation has an explicable rule on the institutional side.

The core question of this paper: is TDCA's engineering structure genuinely isomorphic to its institutional structure, and if so, what are the criteria?

**Core proposition: TDCA's engineering philosophy is not "how to write code" but "how to realize institutional logic as runnable, auditable, fusable machine behaviour".**

As in the institutional philosophy, every engineering proposition here has an **openable registered carrier** in the TDCA repository (⚠️ status governed by `CLAIMS-MATRIX.md`). The institutional philosophy is a philosophical reading of the repository; the engineering philosophy is a repository reading of the philosophy.

## II. Anchor Alignment: The Paradigm of Engineering Scalability

### 2.1 Communication Is Format Compatibility

Communication between people, between systems, and between agents is at root a compatibility problem. Two pieces of software can communicate only if their protocol stacks are compatible; two databases can synchronize only if their schemas are mappable; two agents can collaborate only if their communication formats align.

Format compatibility is not optional; it is the precondition of collaboration. Without it, collaboration is not an efficiency problem but a "cannot connect" problem.

### 2.2 Anchor Economics: From Quadratic to Linear Overhead

There are two ways to achieve format compatibility. Point-to-point conversion needs one converter per pair: N formats require N² converters, which does not scale. Anchor alignment defines a common anchor format to and from which all formats are mapped: N formats require only N mappers.

Data exchange anchors on schema specifications, network communication on layered models, interface interoperability on open specifications, decentralized identity on decentralized identifiers, and agent communication on open protocols — mainstream mature stacks all adopt anchor alignment. The existence of an anchor is the precondition of any scalable compatibility.

### 2.3 TDCA's Four-Layer Anchors: A Trust Chain

TDCA extends anchor alignment from engineering into the institutional layer. The four anchors are not parallel but a bottom-up trust chain:

| Layer | Anchor | Institutional analogue | Engineering function |
|---|---|---|---|
| Physical anchor | Notification machine protocol | The physical layer of a protocol stack | Physically unclonable material, secure-element signatures, hardware identity providing the trust root; physical execution of fusing |
| Attestation anchor | Nested cognitive asset (NCA) attestation chain | Change log | Append-only hash chain: behaviour replayable, independently verifiable, tamper-evident |
| Semantic anchor | Scene quantum | Common schema | Five-domain signature defining the common format of collaboration |
| Scheduling anchor | Configuration-right protocol | Interface contract | The call contract: who may call, with what parameters, leaving what attestation |

Lower layers provide credibility to higher ones: without the physical anchor, the attestation chain's own verification tool hangs in the air; without the attestation anchor, semantic-anchor judgments cannot be traced; without the semantic anchor, scheduling-anchor authorization loses its boundary. The anchors are not four; they are one trust chain from silicon to semantics.

The trust chain also defines the direction of failure propagation and the isolation boundary. Propagation runs downward, isolation upward: a failure at an upper layer does not affect lower layers — a rule revision at the semantic anchor does not change existing records at the attestation anchor, and historical tape is not rewritten as standards evolve; termination of a scheduling-anchor authorization does not reach back into past attestations. A lower-layer failure propagates upward but is bounded: if a single physical anchor is compromised, propagation stops at the attestations issued by that anchor — subsequent attestations issued by that device are refused, existing attestations are marked credible-traceable up to the point of failure, and the device is fused out; **one physical-anchor failure means one device leaves the field, not a network-wide reset**. The branchable structure of the trust chain guarantees a bounded failure radius: contamination stops at the branch, and the institutional trunk does not collapse.

### 2.4 The Divide Between Institutional and Engineering Anchors: Dual Anchoring

Engineering anchors anchor only format: whether the format is right, whether types match. They say nothing about what an exchange is worth. Institutional anchors must **dual-anchor**: they anchor format — whether collaboration is possible — and they anchor value — how much utility the collaboration produces and to whom it is allocated. The latter is carried by the minimum observable utility (MOU) anchoring and the marginal-contribution allocation rule.

This is the essential difference between TDCA's anchors and "yet another interoperability protocol": TDCA invents no new anchor; it extends the mature paradigm of code-level format compatibility into the institutional layer and adds to the anchor a dimension that engineering anchors never carry — utility. The format anchor lets heterogeneous systems connect; the utility anchor makes the collaboration after connection computable, allocable, and traceable.

### 2.5 Anchors Also Need Anchoring

The trust of an engineering anchor comes from standards-body endorsement; the trust of an institutional anchor comes from the three-fold structure of the institutional philosophy. Anchors are not themselves anchor-free: legal anchoring provides a judicial-effect channel for rights confirmation, economic anchoring provides an unforgeable hard floor for utility, and physical anchoring underwrites the whole trust chain — the last layer of the trust root lies in silicon, and the credibility of silicon terminates at the chip package. The anchor of anchors is the recursion of the three-fold structure at the anchor layer.

### 2.6 An Anchor Is Not a Standard

A standard is mandatory, uniform, and refuses difference; an anchor is inclusive, mappable, and permits difference. A standard says "everyone must use the same format"; an anchor says "everyone keeps their own format, and as long as it maps to the anchor, it can connect".

TDCA chooses anchors rather than standards, which is the root reason it adapts to heterogeneous agents, scenes, and data sources. This is structurally isomorphic to federalism: the anchor is the minimal common denominator of the sovereign layer, and mapping is the autonomous coordinate chart of the scene layer. Anchor alignment lets TDCA accommodate difference; difference accommodation lets TDCA cover heterogeneity.

### 2.7 Four Preconditions for Anchors to Land

1. **Controlled evolution**: anchors evolve through institutional increments — explicit versioning, backward-compatible adaptation layers, grey-scale switching. Stability is not freezing; anchor stability is versioned stability.
2. **Verifiability**: results mapped to the anchor must be independently verifiable — depending on the tamper-evidence of the attestation anchor and the judicial effect of legal anchoring.
3. **Human comprehensibility**: an anchor must have both a machine-readable and a human-readable layer — "development, not white-boxing" landing at the anchor layer.
4. **Attributability**: every anchor interaction must answer "which execution entity, representing whom, who is responsible" — anchor alignment must not create a responsibility vacuum.

## III. Data as Flow: The First-Order Object of Engineering

### 3.1 Data Is Not Firmware but Flow

Traditional data engineering treats data as firmware — collect first, then store, then govern, then call. Data is treated as a static asset, and the goal is "to manage the data well".

But the nature of data is not firmware but flow:

- Data is continuously produced, continuously moving, continuously decaying.
- The value of data lies not "in being there" but "in being used by whom, in what scene, producing what utility".
- Managing flowing data as firmware is like managing a river with a warehouse: one can only hold a stretch, never the whole direction.

### 3.2 The First-Order Object Moves from "Data" to "Data Flow"

This shift directly determines the architecture:

- Old architecture: tables, fields, records as the basic units; ETL, warehouses and lakes as the infrastructure; batch processing and periodic synchronization as the mode of operation.
- New architecture: data streams, events and call traces as the basic units; the NCA attestation chain, scene quanta and configuration-right scheduling as the infrastructure; real-time processing and immediate anchoring as the mode of operation.

TDCA's first-order object is not "data" but "data flow". This is the fundamental divide between TDCA and all traditional data engineering.

Further: TDCA's flow is **flow with an institution**. Every passage of data through a scene quantum is judged once, metered once, attested once by the scene function — not a bare flow, but a flow that leaves a trace on every passage. The institutional capture of data flow has the same source as the institutional philosophy's "judging by traces, not by minds": every segment that passes is required to leave a trace, and the accumulation of traces constitutes a credible history.

### 3.3 Flow Naturally Seeks Scenes

Data flow does not move indifferently. It naturally moves toward where it can be used, produce utility, and be priced. That "place" is the scene.

The driver of flow seeking scenes is **economic**: only within a scene quantum can flow be metered by a utility function, priced by allocation rules, and confirmed as a cognitive asset by the NCA. Outside a scene, flow is only cost; inside a scene, flow is value. "Only knowledge that is called has value" — the engineering expression of this institutional proposition is the spontaneous convergence of flow to scene quanta.

Engineering implication: TDCA's architecture need not dictate "where data flows"; it need only define scene quanta, and flow will naturally seek scenes. The scene quantum is the "centre of gravity" of flow — the gravity comes from utility functions and allocation rules, not from administrative compulsion, and the scene quantum is not a "compulsory pipe" for flow.

## IV. Scene as Function: The Second-Order Object of Engineering

### 4.1 A Scene Is Not a Description but an Executable Function

If a scene is only a verbal description ("a customer enquiry scene"), an execution entity cannot execute it. It can understand "this is a scene" but not "what flow may enter, what operations may be performed, what boundaries may not be crossed, to whom the utility belongs".

A scene must be a function — defining input domain, output domain, constraint domain, permission domain, and audit domain at once.

This is the first principle of TDCA's scene engineering: without functionalized scenes, an execution entity can only execute by guesswork; with functionalized scenes, it can execute by declaration.

### 4.2 The Five Domains of a Functionalized Scene

- **Input domain**: what flow this scene accepts (fields, format, source, timeliness).
- **Output domain**: what utility this scene produces (judgments, actions, reports, revenue).
- **Constraint domain**: what this scene's negative space is (operations absolutely not to be performed, data absolutely not to be touched).
- **Permission domain**: who may call what functions in this scene (the configuration-right boundary).
- **Audit domain**: what attestation each call leaves (input/output hashes in the NCA).

Together the five domains are the complete signature of the scene function. Reading this signature, an execution entity knows what to do, what not to do, and what to leave behind.

### 4.3 Isomorphism between Functionalized Scenes and the Institutional Philosophy

The institutional philosophy says "a scene is the minimal configuration unit".
The engineering philosophy says "a scene is the minimal executable function".

The two are isomorphic: the configuration unit is the institutional expression, the executable function the engineering expression. One thing, two perspectives.

This is the direct embodiment of institutional–technical isomorphism at the scene layer — the institution's configuration unit is the engineering's executable function.

## V. Execution Entities Read Functions: The Executing Subject

### 5.1 An Execution Entity Is Not a Reasoning Subject but an Executor of Functions

In TDCA's engineering system, the core capability of an execution entity is not "reasoning" but "reading functions, scheduling configuration, leaving attestation".

- **Reading functions**: the entity reads the five domains of a scene function and understands the input requirements, output requirements, constraint boundaries, permission scope, and audit requirements of the current scene.
- **Scheduling configuration**: through configuration-right scheduling, the entity obtains authorization to call functions, access data, and trigger actions in this scene.
- **Leaving attestation**: every call the entity makes leaves a tamper-evident trace through NCA attestation.

The entity's "intelligence" lies not in "how deeply it thinks" but in "how accurately it executes and how completely it attests". This is fully isomorphic to the institutional philosophy's "judging by traces, not by minds".

### 5.2 The Entity's Execution Boundary Is Defined by the Function, Not the Model

- Old paradigm: give the entity a large model and let it "decide for itself what to do".
- New paradigm: give the entity a scene function and let it "execute within the function's boundary".

Model capability is upstream and not what TDCA sets out to solve. What TDCA solves is this: let the execution entity execute by function within a scene and leave an auditable trace. However strong the model, if it does not execute within the function's boundary, its behaviour is not credible in the TDCA system.

### 5.3 An Execution Entity's "Identity" Is Not an Identity but an Admission State

The institutional philosophy says "do not issue identities to AI; issue an NCA attestation for every call".
The engineering philosophy says "an execution entity's identity field is not an identity but an admission state".

- What the field records is not "who it is" but "whether it has passed admission compilation, and whether it is active in a given scene".
- Updating the field is not "lifecycle management" but "migration of admission state".
- Invalidating the field is not "deregistration" but "termination of admission state".

This is TDCA's core critique of "agent identity management": identity management is an ontological error; admission-state management is engineering correctness. Engineering instance: the notification machine's seven-state machine (unregistered, registered, certified, active, degraded, suspended, fused) records nothing but carrier states of functional admission, and none of the seven answers "who it is".

### 5.4 Fast and Slow Systems: The Adjudication Split in Engineering

Reading functions, scheduling configuration and leaving attestation are all **fast-system** actions — millisecond deterministic automation: configuration-right scheduling, negative-space fusing, the metering engine, secure-element signatures, carried by the compiled execution core and responsible for 99.9% of the system's deterministic operations. But the fast system's legitimacy comes from the **slow system**: human value judgment — revision of the negative-space list, incremental institutional upgrades, adjudication of exceptions.

The engineering structure of the split: the execution core provides the adjudication layer with an irrefutable evidential basis (attestation, metering, fuse evidence packages), compressing human decisions into manageable boundary cases; each conclusion of the adjudication layer (human sign-off and institutional re-review) flows back into the execution core as a new function signature. The fast system must reserve exception-reporting interfaces and human-intervention fields for the slow system — a fast system with no slow-system landing point is a hijackable fast system; a slow system with no fast-system evidence is a seat-of-the-pants slow system.

Engineering instances: secure-element signatures are fast-system evidence collection, while full attestation and human sign-off are slow-system adjudication; the chip-side eight-field condensed attestation is the fast/slow division of labour on constrained hardware — the fast system leaves an evidence digest on-die, the slow system completes the trajectory on-chain. **Fast and slow are not a performance division of labour but a legitimacy division of labour.**

### 5.5 The Physical Trust Root of Attestation: Three-Fold Anchoring on the Engineering Side

The institutional philosophy establishes the three-fold structure: an internally verifiable closed loop, external three-fold anchoring (legal, economic, physical), and the human signature right. The engineering philosophy must answer: what are these three on silicon and in code?

**Engineering counterpart of the internal loop**: the three compiled execution-core components (negative-space enforcement, attestation, fusing) plus a daemon form a dual engine — a Python orchestration layer plus a compiled execution core: the orchestration layer is slow, the execution core fast; institutional logic is deterministically executed on the fast side and human-scheduled on the slow side.

**Engineering counterparts of external three-fold anchoring**:
- **Legal anchoring** carriers: the rights-confirmation interface and the judicial access channel, providing out-of-system adjudication for rights confirmation;
- **Economic anchoring** carriers: the utility metering module and the tax-anchoring interface, currently running on simulated parameters and honestly labelled, to become hard data once truly connected — the simulated label is itself the honest engineering expression of economic anchoring;
- **Physical anchoring** carriers: the notification machine — a protected storage partition that forbids direct user-space writes, secure-element signatures over institutionally sensitive data, physically unclonable key material that never touches disk, and physical fusing running on a dual track with institutional fusing whose irreversibility is auditable. The term "trust root" must here be made precise, to avoid circular argument: the trust of physical anchoring **does not come from the chip itself** — a chip does not certify itself. Its trust chain is: the national commercial-cryptography certification system (algorithm standards, secure-element testing and certification, supply-chain audit) underwrites the physical implementation within the package, and the physical implementation underwrites the attestation behaviour. Physical anchoring is not the starting point of trust but the **execution terminus** of institutional trust in silicon; the trust chain runs from the certification system to the chip package and stops there — not because the inside of the package is absolutely trustworthy, but because the marginal cost of further questioning exceeds the marginal benefit. Trust has a terminus, and the terminus is institutional authorization, not matter itself.

**Engineering counterpart of the human signature right**: the slow system's full attestation and human sign-off column. In the engineering chain, signing authority narrows link by link: the closer to the positive space, the fewer the signing nodes and the more concentrated the responsibility.

The existence of physical anchoring answers the self-reference question on the engineering side: the attestation chain's verification tool runs in a general-purpose computing environment — what underwrites the tool's own credibility? Secure elements and physical fusing. The last layer of the engineering trust root is not in software.

## VI. Configuration-Right Scheduling: The Core Mechanism

### 6.1 The Configuration Right Is Not a Legal Concept but an Executable Function

The institutional philosophy defines the configuration right as φ: O ⊕ U ⊕ C → Cfg (an ordered composition of subject, resource and scene mapping to a configuration). The engineering philosophy realizes this function as an executable scheduling mechanism:

- **Input**: subject (who), resource (what), scene (where), time (when), constraints (what boundary).
- **Output**: authorization (may it be done), parameters (with what parameters), audit requirements (what attestation to leave).
- **Execution**: the entity calls functions within the authorized range, and negative-space fusing intercepts out-of-range calls in real time.

Turning the configuration right from "a legal provision" into "an executable function" is the most direct embodiment of institutional–technical isomorphism on the engineering side.

### 6.2 Three Technical Preconditions for Configuration-Right Scheduling

**Precondition 1: functions must be discoverable by execution entities.** Functions need an open discovery mechanism — queryable through interfaces, declared through scene quanta, exposed through an MCP bridge (MCP is an external open protocol, not an internal component).

**Precondition 2: functions must be composable by execution entities.** Cross-scene collaboration requires function composition. Its preconditions: input/output types must connect, constraints must not conflict, and utility must be additive.

**Precondition 3: functions must be auditable by humans.** Functions are machine-executed, but ultimate responsibility is human. Humans must be able to read, verify and audit functions. A function must not be a black box.

### 6.3 Isomorphism between Configuration-Right Scheduling and the Institutional Philosophy

The institutional philosophy says "the configuration right is the third pole beyond ownership and usufruct".
The engineering philosophy says "the configuration right is the scheduling mechanism of agent collaboration".

The two are isomorphic: the third pole is the institutional definition, the scheduling mechanism the engineering realization. The institution defines the legal status of the configuration right; engineering realizes its runtime behaviour.

## VII. Four Criteria for Institutional–Technical Isomorphism

### 7.1 Criterion 1: Structural Correspondence

Every layer of the institutional structure has a runnable counterpart on the engineering side.

| Institutional structure | Engineering counterpart |
|---|---|
| Scene quantum | Scene-tree mechanism + scene-function signature |
| Configuration right | Configuration-right scheduler + authorization function |
| NCA attestation chain | Append-only hash chain + chain verification tool |
| Negative-space fusing | Four-tier fuse + runtime interception |
| Minimum-observable-utility anchoring | Utility metering module + tax-anchoring interface |
| Shapley allocation | Marginal-contribution computation + revenue-sharing execution |
| Human signature right | Slow-system sign-off column + signing authority narrowed link by link |

If an institutional structure has no counterpart on the engineering side, that structure has not truly been realized.

### 7.2 Criterion 2: Executable Verifiability

Every engineering execution must be verifiable by the institution.

- Every configuration-right call must leave an NCA attestation;
- Every attestation must be independently re-checkable;
- Every re-check must trace back to an institutional rule.

An institution that cannot be verified in execution is a paper institution; an execution that cannot be explained by the institution is a black-box execution.

**Registered carriers**: the chain verification tool, ecological patrol (treating "no attestation" as "did not happen" is the patrol's default adjudication), and field-level reconciliation of audit events — executable verifiability is not a design goal but an **already running check item** (⚠️ per-item status governed by `CLAIMS-MATRIX.md`).

### 7.3 Criterion 3: Traceable Failure

Every engineering failure must be traceable by the institution.

- Out-of-range calls must be fused by the negative space and leave evidence;
- The cause of failure must be traceable to the specific function, scene and caller;
- The trace result must be able to trigger institutional revision (entering the case library through the institutional re-review gate).

A failure that cannot be traced is an unrepairable failure; a failure that cannot be repaired is a slow death for the system.

**Registered carriers**: event sourcing — every state change is written to historical tape and the process is replayable; fuse evidence is automatically archived as a case and feeds back into institutional revision. Failure is not an endpoint but an input to institutional evolution.

### 7.4 Criterion 4: Synchronized Evolution

Every institutional evolution must be realized on the engineering side; every engineering improvement must be fed back to the institutional side.

- An institution adds a constitutional constraint → engineering must add the corresponding checker;
- Engineering discovers a new attack surface → the institution must assess whether a new negative-space item is needed;
- The institutional re-review cycle → engineering must update in step.

Institution and engineering must not come apart. The moment they do, the institution becomes empty talk and engineering becomes an unbridled horse.

**Registered carriers**: institutional increments interlocked with continuous-integration checkers — the trigger directions and reliability constraints are as follows: an institutional document version bump (an online upgrade signed off by humans) produces a new version number; on detecting the version change, the continuous-integration pipeline **automatically** triggers the corresponding checker update and regression tests, and release is permitted only when the regression is green; if engineering discovers a new attack surface, it **must not** modify the institution by itself but must submit to the institutional re-review gate and, after human adjudication, take the same version-bump channel. Each direction has its own trigger: institution-to-engineering is an automatic link, engineering-to-institution an adjudication link. Reliability is guaranteed fail-closed: if an institutional version is bumped while the checker is not updated in step, the release is refused by continuous integration — version alignment is a hard release gate, not post-release remediation. Synchronized evolution is wired into the engineering pipeline rather than left to human diligence.

## VIII. Formal Interface: Where These Propositions Land (⭐ added in V1.4)

The structural propositions established here are all formalizable; ⭐ and the four criteria together with the sections on the trust chain, layering, the admission state machine and the fast/slow split jointly imply propositions **beyond the seven of the formal proof program**. Our side has extracted them item by item and registered them separately; ⭐ this section only points the way (⛔ it does not adjudicate their formal content):

| ⭐ Structure in this paper | ⭐ Formal candidate proposition it generates (plain terms) |
|---|---|
| §2.3 trust chain, failure propagation and isolation | ⭐ **bounded failure radius**: a single point of failure stops at the branch and ⛔ does not cause a network-wide reset |
| §5.3 seven-state admission state machine ＋ institutional philosophy §2.3 layering | ⭐ **admission state machine correctness** / ⭐ **confidentiality-tiered trust roots** (a high-confidentiality scene does not accept a lower-tier trust root) |
| §7.4 synchronized evolution | ⭐ **fail-closed version alignment** (version bump while unsynchronized ⟹ release refused) |
| §2.4 dual anchoring | ⭐ **dual-anchor consistency** (format anchor passes while utility anchor is undetermined ⟹ connectable but not allocable) |
| §5.4 fast/slow split | ⭐ **existence of fast–slow interfaces** (a fast system must have exception-reporting and human-intervention fields) |
| Institutional philosophy §5.2 migration rather than deletion | ⭐ **negative-space migration invariant** (the baseline only grows; items may change position) |

⭐ **Landing note**: the formal carriers and priority sequence of the above propositions (suggested **P1**: admission state machine + confidentiality tiering; **P2**: failure radius / migration invariant / dual anchoring; **P3**: version alignment / fast–slow interfaces) are given in our side's review document; ⚠️ **whether to start work must be explicitly authorized** (⛔ this paper does not adjudicate).

## IX. Conclusion

This paper has argued the core propositions of TDCA's engineering philosophy:

**Proposition 1: data is flow, not firmware.** The first-order object of engineering is not "data" but "data flow" — and flow with an institution: judged, metered and traced on every passage through a scene.

**Proposition 2: anchor alignment is the paradigm of scalability, and institutional anchors must dual-anchor.** TDCA's four-layer anchors (physical anchor, attestation anchor, semantic anchor, scheduling anchor) form a trust chain from silicon to semantics; the essential divide between institutional and engineering anchors is dual anchoring — anchoring both format and utility. An anchor is not a standard: anchor alignment lets TDCA accommodate difference, and difference accommodation lets TDCA cover heterogeneity.

**Proposition 3: express scenes as functions, not as verbal description.** The five domains of the scene function (input, output, constraint, permission, audit) are the complete signature of execution and the landing point of the semantic anchor.

**Proposition 4: an execution entity is not a reasoning subject but an executor of functions.** Its core capability is reading functions, scheduling configuration and leaving attestation; its "identity" is not an identity but an admission state. The fast system executes, the slow system adjudicates, and between them is a legitimacy division of labour rather than a performance one.

**Proposition 5: the configuration right is not a legal concept but an executable function.** Configuration-right scheduling is the core mechanism of engineering and the landing point of the scheduling anchor; the engineering trust root is underwritten by physical anchoring and terminates at the chip package.

Final positioning: TDCA's engineering philosophy is not "how to write code" but "how to realize institutional logic as runnable, auditable, fusable machine behaviour". The institutional philosophy answers "why it is designed this way", the engineering philosophy "how it is realized". The two form a duality and jointly support TDCA as a complete system of "executable institutions".

The four criteria — structural correspondence, executable verifiability, traceable failure, synchronized evolution — each already have **registered carriers** in the repository. And the engineering repository is itself a self-evidencing sample of the institutional philosophy's three-fold structure: frozen files are the collateral of the internal loop, simulated labels are the honesty of economic anchoring, and the sign-off column of every document is the landing point of the signature right. The institutional philosophy says the three-fold structure "is not a claim but a fact that can be verified by opening the repository item by item"; the engineering philosophy completes the sentence: **the repository itself is the object that can be opened and verified.**

## References

[1] TDCA Research Group. TDCA Institutional Philosophy: From the Self-Consistency Paradox to External Anchoring. V1.0 (English), 2026.
[2] TDCA Research Group. Function Whitepaper: A Formal Theory of Institutional Utility Configuration. V2.0-FROZEN, 2026.
[3] TDCA Research Group. Functional Large Models: A Second Paradigm Beyond Parametric Large Models. V1.1-FROZEN, 2026.
[4] TDCA Research Group. Judging by Traces, Not by Minds: A Trustworthy Multi-Agent Collaboration Protocol. V1.0-FROZEN, 2026.
[5] TDCA Research Group. Execution-Core Engineering Repository: negative-space enforcement / attestation / fusing / daemon. V1.0.0, 2026.
[6] TDCA Research Group. Dual-Protocol Compounding Engine. V1.1, 2026.
[7] TDCA Research Group. Runtime Data-Flow Gating Component (data gating and context provisioning). 2026.
[8] TDCA Research Group. Notification Machine Protocol Package (system specification / firmware metadata specification / compliance review report). V1.0 FROZEN, 2026-08-11.
[9] TDCA Research Group. Formal Proof Program: The Meta-Function Development Theorem. V1.0-draft, 2026.
[10] TDCA Research Group. Review of the Two Foundational Papers: Standardization and Extract of Formal Follow-up Propositions (internal). 2026.

> ⚠️ **Citation note**: the propositions in this paper are our own structural claims; ⚠️ references [5]–[8] are their **engineering background sources** (⛔ not quoted sentence by sentence); ⭐ [9][10] are **registered pointers** for the formal interface. ⚠️ Where the body does not cite sentence by sentence, this note governs.

---

**Document status**: **V1.0 (English)**. Under TDCA discipline, the mechanisms described here are **design-state and philosophical propositions**, not claims about the running system; all formal status is governed by the repository files `CLAIMS-MATRIX.md` and `OPEN-PROBLEMS.md` as the **single source of truth**.

## Revision History

| # | Revision | Nature |
|---|---|---|
| 1 | §4.4 added, "Fast and slow systems: the adjudication split in engineering" — fast/slow as a legitimacy division of labour, with three engineering instances | substantive: completes the engineering organization principle |
| 2 | §4.5 added, "The physical trust root of attestation" — item-by-item duality with the institutional philosophy's three-fold structure | substantive: closes the sister-paper duality |
| 3 | §2.2 highlights "flow with an institution" | precision |
| 4 | §2.3 highlights the economics of flow seeking scenes | precision |
| 5 | Criteria 2/3/4 each gain a carrier paragraph | precision |
| 6 | Conclusion adds the duality coda | structure |
| 7 | Internal codes converted to plain names | readability |
| 8 | Abstract and positioning updated to "sister paper" | structure |
| 9 | Chapter II added, "Anchor alignment: the paradigm of engineering scalability" | substantive: the core proposition enters the paper |
| 10 | §2.3 anchors layered into a bottom-up trust chain | precision |
| 11 | §2.4 dual-anchoring divide: institutional anchor = format + utility | precision |
| 12 | §2.7 precondition 1 "stability" made precise as "controlled evolution" | precision |
| 13 | Conclusion expanded from four to five propositions | structure |
| 14 | §2.3 adds "failure propagation and isolation" | polish: bounded failure radius |
| 15 | §4.5 corrects "trust root": a chip does not self-certify; physical anchoring is the execution terminus of institutional trust | polish: removes circular argument |
| 16 | §6.4 makes the evolution-synchronization triggers concrete: institution→engineering automatic, engineering→institution adjudicative; fail-closed version alignment as a hard gate | polish: reliability lands |
| 17 | ⭐ Chapter numbering re-sequenced: the third-level subsections of Chapters III–VII renumbered to 3.x–7.x (⛔ no content change) | compliance |
| 18 | Standard document head and discipline statements added | compliance |
| 19 | Version chain normalized to V1.0 (English) | compliance |
| 20 | "Verified carriers" uniformly changed to "**registered carriers**" with status qualification — ⛔ to avoid being read as "proved" | red-line compliance |
| 21 | First-occurrence terms spelled out in full (NCA, MOU) | terminology consistency |
| 22 | References extended with [9][10] and a citation note added | citation interlock |
| 23 | ⭐ §VIII "Formal Interface" added (six-item mapping) | structural strengthening |

> ⚠️ The present edition is the **public (English) version**: public head, terms per the five terminology rulings, references as plain titles without internal document numbers; ⛔ **no philosophical proposition has been altered in substance**.
