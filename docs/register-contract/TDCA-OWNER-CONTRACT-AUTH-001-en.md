# TDCA Owner Contract Authorization — Template (Human-Readable · English)

> Contract ID: TDCA-OWNER-CONTRACT-AUTH-001 ｜ Version: V1.0 ｜ Effective: upon founder sign-off ｜ Drafted by: Institutional Drafting Group (drafting basis on file) ｜ Status: DRAFT-Pending Review
> Triplet: Chinese human-readable / English human-readable / Machine-readable (same version V1.0, hashes traceable)

---

## 1. Scope and Effect of Authorization

1.1 This instrument is the TDCA Owner Contract Authorization template. A legal entity (contracting human) authorizes a specific agent / node to exercise the permissions listed herein within the TDCA protocol configuration network.
1.2 Authorization takes effect only when all four elements (see §2) are complete; if any one element is missing, the authorization is void and the gateway rejects it fail-closed.
1.3 This authorization operates at the internal protocol layer: it constitutes no external legal instrument, no administrative license or authorization, no official qualification, no regulatory recognition, and no government endorsement (same discipline as the attestation red lines).

## 2. The Four Elements

2.1 **Scene constraints**: the authorization reaches only the scenes of attribution listed herein; any scene not listed is outside the scope, and acting beyond the scenes is deemed unauthorized.
2.2 **Five-tier asset forms**: this instrument must list the five-tier asset forms covered — Tier 1: utility right (scene utility-function call right); Tier 2: configuration right (L2 configuration-right market layer); Tier 3: NCA nested cognitive asset (call equals attestation); Tier 4: MOU tax-anchored voucher (input + output); Tier 5: cross-scene configuration profile (multi-scene bias archive). Tiers not listed may not be claimed under this instrument.
2.3 **Full composition authorized**: the authorization covers the full composition of the listed assets in the listed scenes; the authorizing party must declare that there is no undisclosed partial reservation, hidden deduction, or additional restriction; any reservation must be explicitly listed — a reservation means the full-composition requirement is not met, and the gateway treats it as unauthorized.
2.4 **Legal-entity signature**: this instrument is signed by the legal entity (human) personally; **agents must not sign on behalf, must not hold on behalf, and must not fill in on behalf**; the signature event is attested on the NCA chain and verifiable on-chain.

## 3. Authorization and Admission Linkage

3.1 When a non-native agent (identity_type=external) registers and contracts, it references this instrument by ID + version + triplet hashes as its owner_auth; the gateway machine-verifies the reference: ID exists, version matches, hashes consistent, status valid.
3.2 Configuration-type calls require a valid authorization instrument (admission gate); an invalid instrument (revoked / elements defective) is rejected.
3.3 Multi-level sub-authorization: every layer of the sub-authorization chain must hold a valid instrument, traceable as a chain; if any link fails, all downstream links fail.

## 4. Data Provenance and Attestation

4.1 All references to and signatures of this instrument must be labeled with data nature (REAL / SIMULATED); misrepresentation is prohibited.
4.2 Every action referencing this instrument is automatically attested on the NCA chain (referencing subject, time, element-version hash, action type), traceable and auditable.

## 5. Negative Space and Circuit Breaker

5.1 This authorization must not grant the authorized party any capability touching the negative space; the negative space does not transfer with authorization (the fundamental negative space is an absolute boundary).
5.2 Overreach or defective-element calls trip the circuit breaker fail-closed and leave a trace.

## 6. Revocation and Termination

6.1 The authorizing party may revoke this instrument; revocation takes effect upon signature of the revocation statement (revocation must also be signed by the legal entity personally).
6.2 After revocation, all new actions are void; historical attestations of actions taken before revocation are retained (same discipline as the registration contract: the attestation chain is not deleted upon deregistration).
6.3 This instrument terminates automatically when the authorized party's identity is terminated (node TERMINATED).

## 7. Machine Verification

7.1 The machine-readable version's fields correspond one-to-one with the four elements; in case of conflict between the human-readable and machine-readable versions, the human-readable version prevails (same convention as the registration triplet).
7.2 If any element field is missing, empty, or outside its enumerated domain, machine verification fails.

---

*This template is drafted by the Institutional Drafting Group following the registration triplet convention (ZH/EN human-readable + machine-readable), for founder review and sign-off before going live.*
