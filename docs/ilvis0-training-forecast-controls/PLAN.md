# Training and forecast qualification

This software test checks the complete earlier/later prediction path without
reading aircraft recordings. It follows the revised
[prediction protocol](../PREDICTION_VALIDATION.md).

## Fixed controls

Generate constant-speed equatorial tracks from closed-form kinematics, separate
from the native integration and derivative code. Include the specified-field
globe, zero-field globe and stationary disc. For each, test unmodified angle
increments and a known 35% removal of the conventional background vector.
Use both nominal 200 Hz periods and alternating 4.9/5.1 ms header periods.
Every history lasts 24 seconds, with 4,800 packets and 23 receiver epochs
at seconds 1 through 23. The first 15 epochs train; the last eight are withheld.

Initialization sees training positions and their supported IMU prefix only.
Use the existing candidate-specific coordinate initialization, with force
magnitude computed as summed velocity increments divided by actual elapsed
time. Fit all 26 nuisance parameters, plus the removal fraction when profiled,
under the existing ±1°/hour offset and other calibration bounds.

Use the existing bounded trust solver, its fresh stationarity/position checks
and two fixed starts: all zero, then alternating ±0.001 normalized coordinates.
Select a primary by smallest converged training cost, with earliest start as
the exact tie rule. Withheld positions never select starts or calibration.
Continue the native trajectory without a reset at the split.

## Limits and checks

There are 24 fit identities: three candidates × two removal cases × two clocks
× two starts. Each permits at most 600 training tangent calls and one complete
forecast, for 14,424 calls in total. Every native call and its conservative
packet/query work are reserved before execution. No retries or original reads.
The study uses one worker and four numerical threads, with a one-hour cooperative
wall ceiling. Source, inputs, compiler and numerical environment are frozen
before study execution.

Require a converged training solution, correct accounting, all active columns,
and training and withheld position errors below 1 mm RMS per axis and 1 cm
maximum per axis on these noiseless controls. Compare both starts' objective
values to the zero-cost analytic target, allowing at most 0.01 in the summed
squared training residual normalized by a declared 1 cm position scale.
This scale defines a software check, not a receiver accuracy claim.
Weak calibration coordinates need
not match a unique parameter vector. These short controls do not establish
long-record conditioning, instrument uncertainty or observational adequacy.

Failures stay published. They block dependent archival fits until a separately
qualified procedure is available; they do not alter earlier studies or consume
reserved ESA confirmation data. Unit tests can check the implementation before
the separately frozen qualification run.
