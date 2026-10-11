# Matched NASA integration comparison

This is a separate development study. Preparation authorizes no observed fits.
The completed archive analysis and all previous trials remain unchanged.

## Question and fixed recording

An IMU (inertial measurement unit) records turning and acceleration. Independent
software controls found that accounting for motion within a recorded interval can
greatly improve recovery of a known gyro offset. This study asks whether the same
integration alternative changes the calibration trade-off or model ranking in an
actual NASA recording.

Use the entire previously selected 438-second stretch `570b37d23af5e245dd461051`
from `ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21. Median ground
speed is 878.06 km/h; minimum is 859.55 km/h. Reuse its frozen selection and extraction
provenance. Do not select another stretch using fitted gyro residuals.

The reference is the [completed packet-header clock comparison](../ilvis0-clock-trial-20261010/README.md).
All six reference fits converged. Reuse them without refitting or warm-starting
the new fits from their solutions.

## Equal comparison

Fit rotating globe, still globe and the specified stationary disc under each of the
existing two processing cases: fixed-zero and profiled upstream Earth-rate removal.
Keep packet-header intervals, original integer increments, physical conversions,
mount transformations, receiver observations, covariance, initialization, original
solver and every calibration bound unchanged. In particular, retain the ±1°/hour
constant gyro-offset bounds. These are sensitivity assumptions, not measured unit limits.

Change only integration and its derivatives. The alternative uses the separately
tested `combined` coning/rotating-force calculation, explicitly assuming
`ordinary_rate_integrals`. It estimates within-packet slopes from adjacent packet
averages; it creates no interpolated measurements and does not alter originals.
Three-packet support and the first/last packet treatment follow the frozen candidate.
Already-compensated increments must not receive this correction again.

The [latitude/convention controls](../ilvis0-latitude-controls-20261011/FINDINGS.md)
passed 24 fits, including opposing starts, roll, unequal timing and both hemispheres.
All 27 derivative columns passed the [independent finite-difference check](../ilvis0-latitude-controls-20261011/DERIVATIVES.md).
These checks qualify this calculation for a bounded comparison. They do not establish
unique calibration, a global optimum or Applanix's proprietary increment convention.
Lower residuals alone cannot establish which preprocessing was applied onboard.

## Finite allowance and recovery

Request six starts, one per model/processing identity, with **200 native sweeps per
start and no retries**: at most 1,200 sweeps. Count attempted passes even if they fail.
Reserve the final two sweeps for predictions at the fitted parameters under the
alternative and original integrations. The conservative-covariance diagnostic only
reweights the alternative residuals; it does not fit or integrate again.

Estimate 90–120 minutes at the ceiling, based on reference throughput plus correction
overhead. This is a runtime estimate, not an extra allowance. Use one worker and two
numerical threads total. No other observed study may run concurrently.

Before any launch, verify the reference's completion and evidence receipt, the
qualification receipts, source/input hashes, numerical environment and native build.
Preserve full repository paths in source snapshots so identically named files remain
distinct. Seal the selection, plan, implementation, tests and compiler/build metadata
in a new manifest. Changed inputs or sources require a new freeze and allowance.

Hold an exclusive lock through preparation/launch and worker execution. Append and
fsync each start before fitting. Save hashed results and residuals atomically.
A restart may reuse verified completed identities and start remaining uncharged
identities only. A charged start without a saved result remains an interrupted failure;
its allowance cannot be recovered or retried. A completion record prohibits restart.
The detached worker runs publication after completion. Packaging never extracts,
integrates or fits measurements.

## Report and interpretation

For all six identities retain objective, convergence/stationarity, native sweep count,
elapsed time, parameters, active bounds and local singular values. Preserve failures.
Save receiver-epoch residuals and covariance/residual diagnostics. Compare objective,
horizontal/vertical RMS, Z gyro gain and offset, and boundary count with the unchanged
reference. Also save the original-integration residuals at the new fitted parameters;
label these fixed-parameter predictions separately from the reoptimized reference.

Compare the globe family against the disc first. Reveal rotation only when every
required fit converges and shape consistently favors globe. Report robustness across
both integration treatments and both processing cases, without counting these matched
fits as independent replications. All scientific decision flags remain abstentions.
Numerical completion, residual adequacy and statistical calibration remain separate.

This study authorizes no corpus rerun, bound changes, production promotion or new
rotation-field fits. Assess the result before planning a separately budgeted replication.
