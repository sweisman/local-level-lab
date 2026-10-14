# Recovery of cost-only numerical failures

**Completed: 83/86 fits passed in 891 native sweeps and about four hours.** Both
controls and all twelve repeats passed. Nine more stretches have complete model
comparisons; three remain unfinished after exhausting their primary allowances.
The combined findings are **41 globe preferences, zero flat and 12 unresolved**
among the original 53 selected stretches. [Results](RESULTS.md) preserve every outcome. The [paired precision qualification](../ilvis0-paired-precision-trial-20261014/RESULTS.md)
passed all 16 fits, including both controls and both repeats, with unchanged
physical assumptions and numerical tolerances.

This separate study applied that qualified arithmetic to **all twelve remaining
stretches whose failed stopping checks concern only relative objective change**.
Two have complete primary fits but an unfinished repeat. Selection uses saved
failure types, never a preferred model or a low objective value. The other nine
stretches have stationarity or position-stability failures and are excluded from
this particular recovery. [The inventory](remaining-stretches.csv) records every
remaining stretch and its inclusion or exclusion reason.

Each selected stretch received all three physical models under both processing
assumptions, followed by its original predetermined perturbed-start repeat.
Two previously completed recordings provide fresh controls. Every start uses the
frozen primary endpoint; repeats never replace primaries. The whole selected
interval, measurements, bounds, weights, integration clock and stopping limits
remain unchanged. Earlier evidence and failures remain preserved.

The [finite plan](PLAN.md) caps the study at **86 starts and 5,532 native sweeps**,
using one worker with four numerical threads. There are no retries or automatic
budget increases. Journals charge work before execution; exclusive locks and
hashed atomic outputs support safe recovery after interruption. A completed study
cannot restart. Evidence packaging is complete. The freeze is closed; unused allowances cannot be reused.

A numerical preference requires all six primary fits, its scheduled repeat and
both controls to pass. Partial comparisons remain unresolved. This study does not
calibrate statistical significance, prove a global optimum or identify the
physical cause of the background rotation field.
