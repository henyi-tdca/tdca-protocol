# Regulation on Identity Trust Level Determination

**Version** V1.0 (effective 2026-10-11) ｜ **Revision** promoted from draft; articles unchanged

> **Boundary for external use**: the title and the four tier names may be used publicly. It is **not permitted** to claim that this Regulation "conforms to or is equivalent to" eIDAS / NIST / ITU or any other external framework; correspondence with international levels is **reference only** and constitutes no claim of equivalence.

---

## Article 1 (Purpose)

This Regulation determines the **identity trust level of signals issued externally** — that is, it ascertains which trust level the "trusted root device" behind a signal occupies, and decides **recognition, admission and configuration** accordingly.

## Article 2 (Basis)

This Regulation is made on two long-standing recorded positions: that the **root-node notification device token is the highest trusted root**; and the doctrine of **traceable root form**, which takes as its criterion whether "legally admissible evidence of physical change of the anchoring root" can be produced.

## Article 3 (Terms)

| Term | Definition |
|---|---|
| **Trusted root device** | The **root** that issues the signal (on our side, the root-node notification device; externally, an external hardware or institutional root) |
| **Device uniqueness** | Whether that trusted root device **is the only one** |
| **Physical-address mobility** | Whether that device's **physical address is retained** |
| **Traceable root form** | The form of a root, judged by **whether legally admissible evidence of physical change of the anchoring root** can be produced |
| **Trust information** | Information usable to determine identity trust level (see Article 12) |

Note: The word "**level**" in this Regulation refers **exclusively to identity trust level** (strength of identity assurance). It has **nothing to do** with "levels" in the authorisation or compliance-review sense, and it is **not** the level of title registration (title registration has no levels).

## Article 4 (Scope)

Applies to **all signals entering this configuration network** (our side and external). It **does not concern** public searchability of registration instruments, which follows the separate registration-publicity position.

---

## Article 5 (Tiers — four)

Identity trust levels have four tiers: **Fixed-anchor ／ Movable-anchor ／ Named ／ Below threshold**.

Note: The last tier is **not** called "untrustworthy" (to avoid pejorative characterisation); **"anonymous" does not mean "has no identity"**.

## Article 6 (Determination)

The **sequence** of determination is:
1. Take two attributes: **device uniqueness** and **physical-address mobility**;
2. **Unique and address retained** ⟹ **Fixed-anchor**;
3. **Unique but address movable** ⟹ **Movable-anchor**;
4. **Not unique, but holds a registered real-name authenticated account** ⟹ **Named**;
5. **IP only** ⟹ **Pending supplementation** (alert raised); **anonymous** ⟹ **Below threshold**.

Rules: **missing either attribute lowers the tier**; **tier may not be set on "type of root" alone**; **roots of the same type are not necessarily of the same tier** (evidence decides).

*This article guards against: grading by what a device looks like rather than by evidence.*

## Article 7 (Verification)

1. Verification of the two attributes belongs to the **first gate** (passing root inspection and setting the level);
2. Verification **precedes determination**; those failing verification are **not graded and may not enter the network**;
3. The specific verification requirements (evidentiary method and credential form) are **determined separately**.

## Article 8 (External hardware as anchor)

An external hardware anchor **must pass review and be graded case by case** — **no automatic same-tier treatment, no batch inclusion**. The core of review is whether that anchor can provide **legally admissible evidence of physical change of the anchoring root**.

## Article 9 (Treatment of anonymity)

1. Anonymous subjects are **not graded** and **not admitted** (consistent with the recorded admission rule that failure is a refusal);
2. Clarification: "below threshold" here reads as "**below the trust threshold**", **not "unlawful"**; it does not conflict with the recorded visitor-state arrangement;
3. "Not admitted" here refers **only to admission to the configuration network** (the second gate).

## Article 10 (Standing of real-name accounts and IP)

1. The **primary basis** for the Named tier is a **registered real-name authenticated account**;
2. **IP alone does not constitute sole identification** — IP can be shared, dynamically assigned, proxied or address-translated — and is therefore **an auxiliary signal only**;
3. A subject holding **only a unique IP without a real-name account** is **Pending supplementation**.

*This article guards against: treating "the same address" as "the same person".*

---

## Article 11 (Alert and pending supplementation)

1. **Criterion**: where the only trust information in the on-chain record is **IP** (all else missing) ⟹ **an alert is raised**;
2. **Handling**: an alert is issued; the authority **does not proceed to grade** and **does not silently downgrade**;
3. The alert **must carry a request for supplementary trust information** (it may not be empty); re-determination follows supplementation;
4. Nature: **an alert is not "below threshold"** (it differs from anonymity), and **an alert is not a determination** — it is a **"pending supplementation"** transitional state.

## Article 12 (Trust information)

1. **Trust information** means information usable to determine identity trust level;
2. **Primary basis**: device uniqueness and physical-address retention;
3. A **registered real-name authenticated account** is the primary basis for the Named tier; **IP alone does not constitute sole identification** and is auxiliary only;
4. The list and **minimum requirements** (what suffices to clear an alert) are **determined separately**.

## Article 13 (Three-state handling)

| State | Situation | Handling | Admission |
|---|---|---|---|
| **Gradable** | Trust information present | Grade by the four tiers | Per tier (both gates) |
| **Pending supplementation** | IP only | Alert ＋ request for material | **Re-determine after supplementation** (no grading before) |
| **Below threshold** | Anonymous | Not graded ＋ not admitted | **Not admitted** |

---

## Article 14 (Relation to existing institutions)

1. This Regulation **fills a genuine gap only** (anchor grading ＋ recognition/admission ＋ compatibility maintenance);
2. Matters already covered by existing institutions (admission, dual-track identity, authentication, identity binding, registration publicity) are **referenced only, not rewritten**;
3. Correspondence with international level frameworks is **reference only**; **"equivalent" is not claimed**.

## Article 15 (Recognition, admission and compatibility)

1. **Recognition** of an external identity passes **two gates**: the **first** (passing root inspection and grading) and the **second** (loading the protocol and accepting institutional constraints on entry); the **two gates are not interchangeable**, default order **first then second**;
2. The progression is **recognition → admission → compatibility**; **"mutual recognition" is possible, "mutual re-engineering" is not** — no interference in another's internal affairs, no change of primary keys; **authority to define tiers does not lie outside**;
3. **Territoriality of rules**: a party entering another's system is governed by **that system's standard**; our standard is **not exported**;
4. **Compatibility ≠ "anchor borrowing"** (that term is retired): compatibility means **we adapt proactively to the external access standard**, carried by a **bridge mapping** (internal code ↔ external code), with **primary keys remaining ours**;
5. When the external standard changes, **compatibility changes with it** (a duty to follow).

## Article 16 (Version and effect)

1. This Regulation takes effect on **2026-10-11**, version **`V1.0`**;
2. **Two editions**: this human-readable edition (**authoritative for meaning**) and the machine-readable edition; the two are produced together and cross-referenced by hash;
3. **Amendment follows the append-only rule** — earlier instruments are not rewritten; old versions remain.

---

*This English edition corresponds article-by-article to the Chinese edition (V1.0, 2026-10-11); the Chinese edition is authoritative for meaning. Same version number; hashes cross-referenced; the machine-readable edition may not alter meaning in reverse.*
