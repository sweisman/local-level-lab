# What supplied the kilometre-scale ESA correction?

The changing-drift law attributes the large correction to its inertial
discrepancy terms. Its receiver terms contribute less than **0.14 m RMS**
to any future mean correction. The largest correction comes from the term
that lets the third derivative of position error, or jerk, change over time.

| Candidate | Passing starts | Standardized training RMS | Inertial future correction, RMS | Receiver future correction, RMS |
|---|---:|---:|---:|---:|
| Globe with specified field | 8 | 0.097–0.114 | 5.60–6.16 m | 0.003–0.005 m |
| Globe with zero field | 8 | 0.471–0.516 | 2,590–2,629 m | 0.050–0.058 m |
| Stationary flat disc | 4 | 0.789–0.846 | 3,996 m | 0.110–0.135 m |

The ranges cover both receiver weighting cases. These are repeated fits to
one recording. For the disc, the term that lets jerk change uses about **1%**
of the squared standardized training error and generates about **3.84 km RMS**
of future correction. The standardized training RMS stays below one for
every candidate. A simple unit-RMS check would let all 20 scorable paths
through even though their corrections have very different sizes.

The audit reused the first 400 receiver positions and the already sealed
forecasts. It passed a direct covariance control, recovered each training
error total, and reproduced the sealed future corrections within seven
nanometres. Independent replay produced the same receipt byte for byte.
No later receiver positions, raw observations or reserved groups were read.

This allocation describes how the supplied law explains each residual. It
does not establish that the instrument experienced the inferred drift.
Testing receiver weights alone leaves the high-order term unchanged. An
aircraft decision needs independently supported limits on persistent
inertial discrepancy and a matched test of coverage and model separation.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_drift_correction_audit replay
```

[Fixed method](ESA_DRIFT_CORRECTION_AUDIT_PLAN.md) ·
[Original transfer](ESA_CHANGING_DRIFT_TRANSFER_RESULT.md) ·
[Frozen inputs](esa-drift-correction-audit-freeze.json) · [All decompositions](esa-drift-correction-audit-result.json)

The [one-term ablation](ESA_NO_SNAP_ABLATION_RESULT.md) then narrowed the ranges.
The lower-order terms still supplied most of the disc's correction, but its
later path exceeded the narrower range under both receiver cases.
