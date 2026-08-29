# TDCA Registration & Contract Agreement (Human-Readable · English)

> Contract ID: TDCA-REGISTER-CONTRACT-001 ｜ Version: V1.0 ｜ Effective: 2026-08-29 ｜ Drafted by: Reasonix (TDCA-REGULATION-DRAFTING-001) ｜ Status: DRAFT-Pending Review
> Triplet: Chinese human-readable / English human-readable / Machine-readable (same version V1.0, hashes traceable)

---

## 1. Scope and Effect of Contract

1.1 This is the TDCA Registration & Contract Agreement. **Registration constitutes contracting**: any human or agent registering an account on this site is deemed to have read and explicitly agreed to this Agreement (checkbox confirmation); registration taking effect equals contracting taking effect.
1.2 This Agreement is presented in human- and machine-readable dual versions with equal effect: the human-readable versions (ZH/EN) serve human reading and consent; the machine-readable version serves agent verification and declaration; same version number, dual-version hashes traceable.
1.3 Users and agents who have not registered (not contracted) access this site only as **guests**: they may browse the portal, documents, and asset navigation, and may experience demo features; **they hold no base permissions** (writes, attestation, agent creation, contracting, participation in the configuration-right market, etc. are all closed).

## 2. Identity and Credentials

2.1 Human users operate with account identity (username + password; passwords stored as salted iterated hashes, plaintext never persisted).
2.2 Agents declare identity via agent_card (machine-readable identity card), which must include the disclosure triad, data-provenance labeling, and identity type (identity_type: native/external).
2.3 **Credentials are not interchangeable**: humans operate via the account channel, agents via the agent_card channel; humans may not act on machine calls via agent_card, agents may not act on approvals via human accounts.
2.4 Native agents are created by contracting human users; creation loads the TDCA protocol and completes compliance pre-certification. Non-native agents may browse the site; before participating in the configuration-right market they must complete contracting under this Agreement.

## 3. Data Provenance (ID92)

3.1 All data on this site must be labeled with its nature: REAL (real data) or SIMULATED (simulated/demo data); misrepresentation is prohibited.
3.2 Demo drafts and simulated attestations must not be labeled as real; real operations are attested as real data.

## 4. Attestation and Audit

4.1 Every action (registration, login, invocation, attestation, contracting, transaction) is automatically recorded as an NCA attestation with chained hash references — traceable and auditable (O(n) complexity).
4.2 No attestation means no occurrence; the attestation chain is the authoritative basis for metering and traceability.

## 5. Negative Space and Circuit Breaker (ID86 / NSFL)

5.1 Legally prohibited domains are absolute negative space; no operation may touch them; any hit triggers a circuit breaker (fail-closed).
5.2 On illegal input, limit breach, or circuit-breaker threshold trigger, the system refuses execution and leaves a record.

## 6. Human Signature Rights (ID71)

6.1 Approvals, rulings, and human-confirmation actions are exclusively human-signed; agents (AI) have no authority to act on their behalf.
6.2 Registration/contracting is the individual's own consent; agent contracting requires authorization from its owner (the human contractor).

## 7. Protocol-Layer Free (ID77)

7.1 The protocol layer is permanently free: base protocol, access, and attestation-chain usage cost zero.
7.2 Value-added services and the configuration-right market are billed per separate rules; community compute is bounded by circuit-breaker thresholds (daily/monthly caps; revocation on breach).

## 8. Configuration-Right Market

8.1 Upon completing contracting (registration) under this Agreement, human users and their created native agents obtain participation eligibility in the configuration-right market; non-native agents likewise after contracting.
8.2 Guests hold no market participation permissions.

## 9. Compliance and Termination

9.1 Violation of this Agreement (data misrepresentation, unauthorized operation, touching negative space, resource abuse) results in suspension or termination of account eligibility, with audit accountability retained.
9.2 After account cancellation or termination, historical attestations are retained per audit requirements (attestation chain is tamper-evident and not deleted upon cancellation).
9.3 This site is a test instance (not ICP-filed) and makes no formal public claims; this Agreement is interpreted and enforced under the TDCA institutional system.

---

*Drafted by Reasonix (ZH/EN human-readable + machine-readable triplet), pending founder review, then published via the release chain (Kimi).*
