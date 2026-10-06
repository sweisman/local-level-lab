# Observable flight-domain enforcement — 2026-10-06

The decision artifact now binds an explicit, preregistered observable envelope. This closes
the gap between a calibration's descriptive geometry metadata and operational threshold lookup.
It does not select a scientifically adequate domain, establish error rates, promote a policy,
or enable public-track GPS recovery. No flight campaign or optimizer search ran in this stage.

## Contract

`analysis/lll/flight_domain.py` defines `observable-flight-domain-1`. A descriptor has `version`,
`sources`, `bounds`, and `epoch_start_minutes`. An optional `domain_id` must match its canonical
SHA-256 identity; canonical output always includes it. Exactly one acquisition lane is allowed:
`synthetic_gnss`, `recorded_gnss`, `binned_input`, `replay_observed_fixes`, or
`replay_simulated_high_rate`. Lanes need separate calibration. The analyzer derives the lane
from the recording manifest and refuses an explicit source override.

Every bound is a finite inclusive `[minimum, maximum]` interval. Required properties are
`latitude_min_deg`, `latitude_max_deg`, `speed_min_mps`, `speed_max_mps`, `usable_minutes`,
`elapsed_minutes`, `heading_span_deg`, `max_gap_seconds`, `max_bin_seconds`, `n_bins`, and
`n_epochs`. Each retained mount epoch has one disjoint ordered start-time interval in
`epoch_start_minutes`; the first is `[0, 0]`, and `n_epochs` must equal the schedule length.
No bounds are estimated from accepted outcomes or filled in automatically.

Observables come from the bins actually retained for that fit. Latitude is converted from
radians; speed is the magnitude of GNSS north/east velocity. Heading span is the smallest
circular arc containing GNSS courses, including north crossings. Bin windows are centered
at `t` with width `dt`. Usable duration sums nonoverlapping windows; elapsed duration includes
excluded intervals; the gap metric measures the largest space between retained windows.
Epoch times refer to the first retained bin-window start in each mount epoch, relative to the
first retained window. They are not raw event timestamps or a measure of aircraft heading.
Malformed, overlapping or missing intervals cannot certify membership. These properties
depend on preprocessing/selection but never read fitted gyro coefficients or simulator truth.
They describe a restricted observable envelope, not all possible trajectories within it;
adequate geometry stress coverage still requires scientific review and validation.

## Decision and campaign binding

`fit.fit(..., flight_domain=descriptor)` records `domain_observables`, the canonical
`flight_domain`, recomputable `domain_membership`, and `domain_id`. Outside-domain fits retain
their diagnostics and report `domain_id=null`; the shared primary/pair scientific gate abstains.
Threshold policies can supply the domain automatically, but primary/pair/explicit domains must
agree. Missing or inconsistent bindings abstain. Direct unscoped threshold dictionaries cannot
make an empirical decision. Default analyses without empirical thresholds remain diagnostic.

The research harness accepts `--flight-domain FILE`, embeds its canonical content in candidate
settings and the manifest, and requires it for new flight calibration/validation preparation.
Calibration checks every successful record against this freeze and excludes outside records
without replacing attempts. Primary `empirical-decision-5` keys are
`[candidate_id, variant, model_test_rank, domain_id]`. Flight `pairwise-empirical-3` keys append
the domain to the coordinate or direct-profile key. Direct profiles retain pair-specific rank
handling. Validation requires exactly the same frozen descriptor as calibration.

Historical unscoped calibration artifacts remain readable for offline research; applying them
to a flight now abstains. Old source/environment freezes remain historical. No actual domain or
threshold has been approved. The magnetic two-path candidate still refuses empirical policies
pending its separate calibration rules. Public-track replay still refuses empirical policies
pending position/timing uncertainty work. Summary-level pooling has its own research calibration;
a flight domain cannot be transferred to it, and this stage does not qualify real pooled decisions.

Verification uses independent bin geometry and bounded policy/fit fixtures. It covers inclusive
limits, missing/nonfinite data, source separation, timing failures, altered identities, shared
eligibility, primary/pair threshold lookup, profile rank handling, and validation preparation.
No synthetic flight attempts or independent tail evidence are counted from these software checks.

The combined focused suite passed 156 checks in 29.71 seconds. After adding the domain module
to the scientific source freeze, 70 domain/eligibility/hardening checks passed in 1.14 seconds,
including a regression proving that changes to the domain module alter the frozen hash.
The prior full Python suite applies to the earlier wind/CI commit; it has not been rerun here.
