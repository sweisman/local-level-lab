# Z calibration with possible upstream field removal

The [first joint grid](../ilvis0-z-profile-audit-20261011/README.md) completed
27/27 fits: every tested Z-axis correction preserved globe preference, then the
specified background-field preference. This separately frozen grid changes only
the processing assumption, allowing some standard background field to have been
removed onboard.

An IMU (inertial measurement unit) measures turning and acceleration. This uses the
same complete 438-second IMU21 stretch, median speed 878.06 km/h, from
`ILVIS0_applanix_57300_610_LVIS_38614965.013`. Z gain is fixed at −2%, zero or +2%,
and constant Z offset at −1, zero or +1 degree/hour. All three models reestimate
remaining parameters at each combination, with unchanged bounds, original integration,
packet-header timing and the original solver. The common removal fraction starts
at zero and ranges from zero to one. Each model fits it under the same limits.

The [plan](PLAN.md) permits **27 starts, 200 native sweeps each, 5,400 total,
no retries**. The [sequential launcher](../../analysis/tests/ilvis0_z_profile_sequence.py)
runs this stage then the [preselected other recording](../ilvis0-z-profile-replication-20261011/README.md).
Both locks stay reserved, with one worker and two threads total. The combined ceiling
is 54 starts and 10,800 sweeps, approximately 12–14 hours if both exhaust their budgets.

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_z_profile_sequence.py --prepare-only
```

Preparation hashes sources, inputs and numerical environment; it performs no fits.
The approved sequence launches with `--detach` instead of `--prepare-only`, outside
a short-lived command sandbox. Sequence status and lock are in
`data/ilvis0-z-profile-followups-20261011/`; each stage has its own manifest,
authorization, start journal and completion. Do not edit either freeze while waiting
or running. Interrupted charged starts remain failures; only unchanged, uncharged
identities may resume. Never restart completed studies.

Results publish automatically, including failures, figures, derivatives and epoch
residuals. Completed publication uses `analysis/tests/ilvis0_z_profile_followup.py
--study removal --package-only` in the same environment; it performs no extraction or fits.
Small residuals cannot identify actual onboard removal. Original field and unknown
subtraction remain inseparable without further constraints. Model preferences do
not determine the field's cause; statistical decisions remain abstentions.
