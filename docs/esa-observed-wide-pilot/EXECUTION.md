# Matched observed comparison: frozen scope

## Question

Does the qualified wider numerical calculation improve completion and prediction
on the same ESA development recording, with the scientific assumptions unchanged?

The software prerequisites are complete: all 48 long known-motion controls and
all 24 training/forecast controls qualify. The latter used 268 native calls in
113.96 minutes. The observed adapter and saved-results audit pass 56 checks bound
to the current source and environment.

## Measurements and method

Reuse the original prepared twenty-minute interval from recording 187, with its
saved measurements and hashes. Earlier 800 receiver positions determine the
initial state, calibration, weights and gravity anchor. Later 400 positions
score a continuous forecast after it is saved; they do not adjust it.

Keep all three candidates, both processing assumptions, both working receiver
error policies and both declared starts: 24 fits. The height-gravity law,
calibration bounds, initialization, stopping checks, accuracy limits and
training-only primary selection are unchanged. Wider precision is the numerical
change. No original aircraft file or reserved confirmation recording is opened.

## Separate finite allowance

| Resource | Ceiling |
|---|---:|
| Declared starts | 24 |
| Fit evaluations per start | 200 |
| Forecast calls per start | 1 |
| Total native calls | 4,824 |
| Conservative packet/query work units | 931,458,086,400 |
| Workers × numerical threads | 4 × 1 |
| Cooperative elapsed-time ceiling | 8 hours |
| Retries | 0 |

The time ceiling is a limit, not a runtime forecast or a promise of completion.
It follows measurement of the qualified controls and matches the earlier
observed pilot's ceiling. This is a fresh allowance; no unused allowance is
transferred from earlier work. Starts and evaluations are charged before use.
Interruption does not erase charges. A cooperative limit never signals or kills
a running calculation.

## Reporting

Preserve every failed or incomplete fit and compare each declared start with
the earlier height-gravity result. Select primary starts using training results
only. Assess horizontal and height accuracy together, separately from numerical
completion. Compare shape before the specified-background-field alternatives.

The saved-results audit performs no refit or propagation. It verifies inputs,
source and compiled-calculation provenance, complete calibration columns,
training/forecast boundaries, physical errors, failures and all charges.

This single development recording cannot establish independent replication or
calibrated confidence. Seven ESA confirmation groups remain protected. The
53-stretch findings and all original failure labels remain unchanged.

[Prerequisite plan](PLAN.md) · [Study overview](README.md) ·
[Qualified training controls](../esa-wide-training-controls/README.md).
