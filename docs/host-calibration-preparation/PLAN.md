# Fresh prediction calibration under a host service

**Finite proposed scope; launching requires separate compute approval.** See
the [current preparation and execution status](HOST_PREDICTION_STATUS.md).
The previous calibration
saved 1,813 passing simulated fits but could not supply a threshold after four
starts were interrupted. It remains closed. The proposed replacement uses new
random seeds and a host-managed service that passed the separate launcher-exit
test. No previous allowance is reused.

The scientific question and numerical method stay the same: can the fitted
pipeline predict later generated positions with the planned whole-forecast
coverage? Calibration chooses an uncertainty threshold; a separate validation
cohort tests it. This does not yet establish an error law for actual aircraft
or statistical significance of the Earth-model comparison.

## Finite proposed allowance

| Item | Calibration | Independent validation |
|---|---:|---:|
| Seed families | 299 | 181 |
| Required settings and starts per family | 24 | 24 |
| Maximum fit starts | 7,176 | 4,344 |
| Workers × threads each | 4 × 1 | 4 × 1 |
| Maximum evaluations per fit | 200 | 200 |
| Linear-operation ceiling per fit | 620 | 620 |
| Maximum iterations per linear operation | 100 | 100 |
| Retries | 0 | 0 |
| Cooperative wall ceiling | 240 hours | 144 hours |
| Minimum free disk before launch | 55 GiB | 35 GiB |

At the last campaign's measured rate, calibration is estimated at **153 hours
(6.4 days)** and validation at **93 hours (3.9 days)**, using four numerical
threads. These are extrapolations, not deadlines or promises. The separate wall
ceilings remain 240 and 144 hours. Validation is conditional on a usable
calibration threshold.

Calibration uses seeds 281474977610656–281474977610954. Validation uses
281474977710656–281474977710836. All previously declared cohorts, including
their unused seeds, remain excluded. Calibration and validation have separate
manifests, allowances and journals. Validation cannot start without its own
complete, source-bound calibration handoff.

The numerical ceilings, error process, physical models, calibration bounds,
processing cases and both input laws are inherited unchanged. The four-worker
allocation is the entire permitted numerical allocation while a phase runs.
The original 53-stretch results and protected ESA recordings are untouched.

The frozen cohort policy explicitly requires no interrupted outcomes. A single
lost charged start blocks further continuation of either phase; a completed
unsuccessful numerical start remains subject to the original repeat-selection
rule. This separates an interrupted calculation from a completed poor fit.

## Implementation and qualification

Use the existing `lll.studies` lifecycle and shared calibration executor.
Add `analysis/lll/studies/prediction_release.py` for declarative fresh releases
and the small `analysis/lll/host_prediction_release.py` configuration. Do not
copy a worker, fitter, noise generator or numerical method.

The combined 48-case optimizer qualification remains the numerical prerequisite.
An explicit source bridge permits only the tested interruption-reporting update
in `prediction_calibration_report.py`, with exact old/new hashes. Restore that
one historical hash when verifying the original qualification binding; require
every other qualified source and the environment to match. No mathematical
source is excepted. Preserve all historical reports unchanged.

Reuse the exact hash-pinned original qualification report and verify both sealed
parent completions. Check the current source set through that reporting-only
bridge; do not recompute a historical verdict using changed reporting code.

Before launching, require deterministic checks in
`analysis/tests/test_host_prediction_release.py`: disjoint cohorts, unchanged
noise and bounds, the exact reporting-source bridge, fail-closed handoff and
disk/lease guards. Bind the complete required suite to the new sources and
environment. Independently verify the calibration freeze, exact charges,
storage estimate and host-service command before requesting compute approval.
No saved fit is rerun for this qualification. The current status page records
which preparation gates have passed.

## Execution and storage

Use a uniquely named host user service, the frozen adapter and the shared runner.
Disable automatic restarts. Check leases and completion before every launch.
After an interruption, keep starts charged and use the qualified recovery
checker; never duplicate a worker or restart a closed phase.

The host must remain running, with its user service manager active. Normal
submitter exit was tested; survival of host reboot, container reset or logout
was not. No process is signaled to enforce a deadline. Existing cooperative
checks provide the finite wall allowance.

The disk figures above are launch reserves, not permanent-retention targets.
After completion, hash-verified evidence is deduplicated into bounded archives
and recoverable working copies are compacted. Preserve raw inputs, charged
failures and provenance. Packaging must never refit.

[Recovery qualification](execution-recovery/README.md) ·
[Previous closed calibration](FEASIBLE_PREDICTION_STATUS.md) ·
[Next analyses](NEXT_STEPS.md).
