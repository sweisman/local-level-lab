# The high-scoring calibration proposals fail the earlier fit when linked

The relaxed search on ESA development flight 187 proposed two stationary-disc
points above the **25.41-unit** forecast gap. Reconstructing the saved proposals
showed why they cannot yet serve as evidence that calibration can erase it.

| Disc calibration range | Recovered relaxed score | Largest affine violation at the displayed point | Earlier loss increase after physically linking the terms |
| --- | ---: | ---: | ---: |
| 2/2, child 1 | 29.76 | 1.5 × 10⁻⁹ | 26,985 |
| 3/2, child 1 | 30.38 | 1.3 × 10⁻⁶ | 49,119 |

The allowable increase in earlier loss is **0.01**. Both points sat below
that limit while their calibration terms could move independently. When
those terms came from one physical calibration, the earlier loss rose well
past the limit. The linking check uses the saved trajectory approximation.
The full nonlinear trajectory was not recomputed.

All **11** ranges completed. The 22 linear programs returned 20 points.
None passed every original affine inequality in exact arithmetic. All 20
exceeded the earlier loss limit after physically linking the terms. The
smallest linked earlier loss increase was 24,054. No point establishes a
reversal, and the upper bound remains **53.04 units**. These particular
proposals give the next bound a direction to check. Project the earlier
loss along the residuals from the linked points and evaluate that projection
over the whole physical calibration box. The integration error still needs
a separate bound.

The run took 47 seconds on two one-thread workers. Eighteen focused tests
passed. No new inertial fit, native integration, later receiver measurement
or reserved flight was used.

[Frozen plan](ESA_LINKED_FLOOR_WITNESS_PLAN.md) ·
[All proposed points and checks](esa-linked-floor-witness-result.json) ·
[Execution receipts](esa-linked-floor-witness-evidence/README.md) ·
[Reproduction bundle](esa-linked-floor-witness-evidence/bundle.zip)
