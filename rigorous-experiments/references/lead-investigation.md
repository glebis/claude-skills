# Mode: investigate-leads

After an exploratory sweep or any run produces "leads" (p<0.06, not
FDR-confirmed), investigate them — do NOT list them as findings and do
NOT re-test them at the same scale. The goal is triage: separate the few
candidates worth prospective testing from small-n and regime-step
artifacts.

## The core distinction

**Robust ≠ significant.** A lead that survives leave-one-out at n≈26–31
is still underpowered for confirmation. Most leads from a large sweep are
"robust-but-underpowered" — honest candidates, not findings. Only
prospective replication (a frozen protocol, tested once at a pre-committed
n) confirms.

## The battery (pre-register which apply per lead)

Run `scripts/triage.py` for the project-agnostic checks; add the
trend/daily checks inline.

1. **Leave-one-out robustness.** Drop each unit once. FRAGILE if the sign
   flips OR |r| more than halves on any single deletion — a small-n
   artifact. (Necessary, not sufficient: passing LOO ≠ significant.)
2. **Directionality** (lag leads). The reverse direction must be weaker.
   If reverse |r| ≥ forward |r|, the causal reading dies.
3. **Detrend vs regime-step** (trend leads). A "gradual trend" whose
   two halves have opposite-sign slopes is a STEP, not a trend (this
   killed an r=−0.78 lead). Require same-sign slope in both halves;
   ols-detrend and confirm the residual no longer trends.
4. **Within-stratum / Simpson** (cross-group or cross-cycle trends).
   Re-fit the slope WITHIN each stratum; a cross-stratum trend whose
   within-stratum slopes disagree is a between-regime artifact.
5. **Prewhiten + bootstrap** (daily/trending cross-series). Re-test on
   AR1 residuals and under stationary block bootstrap. A lead that holds
   after prewhitening is a real relationship, not shared trend — this is
   how a lead gets genuinely UPGRADED, not just survived.

## Consolidation (the high-value move)

Several weak leads pointing the same way are often ONE construct.
Combine them into a single z-scored composite and test that — it usually
has more power than any component. Example: three separate therapy trends
(absolutist↑, negation↑, hedge↓) consolidated into one
`z(absolutist)+z(negation)−z(hedge)` certainty/rigidity index at r=0.66,
stronger than any of its parts. A composite is a cleaner prospective
target than three fragile correlations — and it is theory-shaped.

## Output

A triage table with one verdict per lead:
- **known** — re-confirms an established effect (directional, robust);
- **strengthened** — survives prewhitening/bootstrap → upgrade;
- **candidate** — robust but underpowered → prospective protocol;
- **artifact** — small-n / regime-step / Simpson; killed.

Mint NO new "confirmed" here — the battery is diagnostic. Mark the
results file `descriptive_only: true`. Promote candidates only via a
prospective protocol.
