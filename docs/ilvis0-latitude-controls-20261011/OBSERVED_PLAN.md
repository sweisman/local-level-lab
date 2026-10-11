# A small matched NASA integration comparison

**Prepared proposal; this document authorizes no observed starts.** The
[latitude controls](FINDINGS.md) justify testing an integration alternative. Keep
completed studies unchanged and prepare a separate worker and implementation freeze.

## Fixed target and six identities

Use the entire preselected 438-second control `570b37d23af5e245dd461051`, from
`ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21. Its median ground
speed is 878.06 km/h and minimum is 859.55 km/h. Do not reselect using gyro residuals.

Reuse the completed six-fit packet-header clock comparison as the original-integration
reference. Fit six new identities using combined coning/rotating-force compensation:
three physical candidates × the existing fixed-zero/profiled Earth-rate-removal cases.
Preserve raw integer increments, physical conversion, packet order, header intervals,
GPS coordinates/covariance, initialization, original solver, ±1°/hour gyro-offset
limits and all other bounds. Change only integration and its derivatives. Do not
warm-start from a preferred fit or choose a new clock simultaneously.

The new path explicitly assumes ordinary integrated rates. This does not establish
that Applanix measurements require or lack compensation. Report both treatments;
better fit alone cannot identify the proprietary convention.

## Preflight and allowance

Verify all 27 derivative columns against finite differences, including initialization,
all calibration axes, lever arm, latency and profiled removal. This local check does
not qualify unique recovery of 27 parameters or a global optimum.

Verify reference receipts, source/input/environment hashes and native build. Use
one durable worker, at most two numerical threads, an exclusive lock, fsynced
append-only starts and atomic outputs. Interrupted attempts remain charged; no retries.
Publication performs no fits. No completed study's unused allowance is available.

Request **six starts, 200 native sweeps per start including final diagnostic predictions:
1,200 sweeps maximum**. The reference averaged about 3.17 seconds per evaluation,
or roughly 63 minutes at the ceiling before correction overhead. Provisionally allow
**90–120 minutes**; this is an estimate, not a measured new-kernel runtime or retry reserve.
Implement and verify the launcher before requesting permission to run it.

## Reporting

For every candidate/case report convergence, fresh projected gradient, objective,
horizontal/vertical errors, Z gain/offset, other active limits, local singular values
and epoch-level residual behavior alongside the unchanged reference. Retain failures;
an unfinished fit is not completed evidence against its model. Residual correlation
and absolute adequacy remain separate from optimizer completion.

Interpret globe versus the specified stationary disc first. Reveal rotation only
after complete shape comparisons under both processing cases favor globe. This
development comparison asks whether calibration behavior changes and the ranking
survives equal integration alternatives. It does not authorize a corpus rerun,
promote a statistical threshold or establish independent replication.
