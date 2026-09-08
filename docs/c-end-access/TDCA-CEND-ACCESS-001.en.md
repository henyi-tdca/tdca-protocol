# TDCA C-Side Mechanism Establishment · Consumer-Contribution Access to the Configuration-Right Market (Public Document)

> Document ID: TDCA-CEND-ACCESS-001 ｜ Status: ✅ Established (2026-09-08, human ruling chain closed) ｜ Language: bilingual (this file is the English edition; the Chinese edition resides in the same directory)
> Institutional anchors: CCA Consumer-Contribution Access (T-130) ｜ scenario demand signal D_scene (T-131) ｜ Hybrid Configuration Market HCM (T-132) ｜ party-pair completeness coefficient λ_pair (T-133) ｜ Scenario Mutual Recognition SMR (T-134)
> Empirical base: merchant_loop (merchant consumer-benefit toolkit) ｜ dca_sandbox (DCA-reshaped sandbox + R-7 hybrid-market three-party closed loop) ｜ 341 tests passing across the chain
> Data nature: institutional-layer analysis + sandbox simulation (SIMULATED — full simulation before e-CNY integration; no real funds involved)

---

## 0. One-sentence establishment

**The TDCA Configuration-Right Market hereby establishes a formal participation channel for the C side (individual consumers) — "Consumer-Contribution Access (CCA)"**: consumers generate verifiable contribution value through real consumption redemption, and enter the Configuration-Right Market with **demand-side participation rights** (observation / voting / benefit giveback, tiered and upgradable) — **non-token, non-tradable, no appreciation promise**. The institutional design (typology / pricing / settlement) plus the three-party closed-loop sandbox evidence (26-week simulation) is fully closed-loop.

## 1. Why a C-side channel is needed

The original participants of the TDCA L2 Configuration-Right Market were contracting agents and organizations; **individual consumers had no participation channel** — real consumer demand never entered the demand side of the market, yet the MOU underpinning L2 pricing P_C (observable utility) requires exactly such real demand signals. **The established channel**: let consumer demand enter the market as a **verifiable signal**, not as a tradable object.

## 2. The CCA participation mechanism (four-step closed loop)

```
① Consumption redemption (real): C-side real in-store consumption → benefit redemption → merchant turnover NCA-attested
② Contribution accounting:       contribution value = f(amount, redemption authenticity, scenario) → consumer contribution account (NCA chain)
③ Demand-signal aggregation:     scenario-level demand signal D_scene = Σ(contribution value × scenario weight) → on-chain verifiable
④ Market response:               agents/merchants configure production against D_scene (scheduling tax, simulated) → consumers receive giveback / contribution-tier rewards
```

**Participation-right design (no tradable instrument is issued)**:
- **Eligibility**: contribution value reaching a scenario threshold grants observation/voting rights on the demand side of that scenario (not trading rights) — **tiered and upgradable** (observation / voting / giveback tiers rise with real contribution)
- **Weight**: scenario voting weight ∝ contribution value × scenario weight (one-person-one-vote baseline with anti-abuse weighting; per-person annual cap)
- **Giveback**: contribution tier → stacked merchant giveback + ecosystem honors (no return promised)
- **Constraints (the four irreducibles)**: **non-transferable / non-tradable / no cash-out / no appreciation promise**

**Cross-scenario discounting**: conditional on **Scenario Mutual Recognition (SMR)** — where a mutual-recognition rule exists between scenarios it applies (κ≤1, shrink-only); where none exists, conversion is forbidden (fail-closed).

## 3. Institutional coordinates (unified multi-party configuration space)

| Party pair | Participation form | Coverage |
|---|---|---|
| Human–Human | natural-person participation rights (tiered), non-tradable — no resale domain opened | Established (CCA) |
| Human–Organization | organizational contracting + CLS B-side (supply chain) ｜ bilateral consumption (merchant_loop does not enter CLS) | Existing + this establishment |
| Agent–Agent | CCP / micro-delivery (native to the machine-machine plane) | Existing |
| Hybrid (Agent–Human/Organization) | cross-track authorization (1:1 / 1:N matching; N:N forbidden) + three-party closed-loop evidence | **Core of this establishment** |

**Layered pricing**: the P_C kernel is unchanged, plus the party-pair completeness coefficient λ_pair (machine-machine / organizational = 1.0 baseline; hybrid D-person 0.95 / D-org 0.98 calibration — M3 empirical convergence in sandbox); the differential accrues to the circuit-breaker fund.

## 4. Evidence (sandbox verification)

- **DCA-reshaped sandbox**: merchant_loop (benefit publish / redeem / ROI) → 26-week simulation → **graduated from sandbox** (redemption rate ≥60% for 26 consecutive weeks / zero pool breach / 0 violations / activation >1.2)
- **R-7 hybrid-market three-party closed loop**: C-side consumption contribution → merchant benefits → agent matching; 26 weeks × 3 seeds all on target (activation ≈2.20; 0 financialization / 0 signal-purchase / 0 prepaid-retention violations)
- **Subsidy-abuse detection evidence**: the behavioral-layer "signal purchase" channel was caught by the detector (negative-control test) — the defense line works
- All SIMULATED (sandbox evidence, not real commercial outcomes); a real pilot awaits e-CNY integration

## 5. Establishment statement and boundaries

- This mechanism is **TDCA's formal establishment of the C-side participation channel** (consumer signals entering the demand side of the Configuration-Right Market) — no token issuance, not an investment product, no principal guarantee
- Red lines throughout: no-asset trading / no-principal-guarantee / no-fund-pool / no-Ponzi; full simulation before e-CNY integration
- Terminology registered in the TDCA registry (T-130~134); evidence code is open source (see tools/merchant_loop + tools/dca_sandbox)

---

*TDCA C-side mechanism establishment — CCA consumer-contribution access to the Configuration-Right Market ｜ institution + evidence fully closed-loop ｜ related: R-7 multi-party typology study of the Configuration-Right Market (TDCA-TASKBOOK-R7-001)*
