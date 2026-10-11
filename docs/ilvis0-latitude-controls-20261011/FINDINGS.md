# The integration improvement survives both hemispheres

**All 24 software fits passed.** The corrected integration recovered the injected
Z-axis gyro offset within 0.00079°/hour across both hemispheres, all three supplied
physical truths, both starting points and both motion/calibration constructions.
No fitted parameter reached a limit. No NASA recordings were refitted.

An **IMU (inertial measurement unit)** measures turning and acceleration. This test
extends the [earlier comparison](../ilvis0-compensation-controls-20261011/FINDINGS.md)
from the equator to +45° and −45° latitude. Each independently generated track lasts
12 seconds, moves at 220 m/s and stays at 1,000 m. Background rotation and transport
vectors are calculated separately from the production predictor.

The interior construction uses regular spacing and pitch/yaw. The near-boundary
construction adds roll, unequal spacing and calibration close to its limits. Each
runs from zero and a deliberately opposed initial guess. Because the second
construction combines several changes, this checks robustness rather than assigning
an improvement to any one of them.

At the known calibration, original integration produces about 41 micrometres of
maximum position error in the interior controls and 225 micrometres in the roll
controls. Both corrections together reduce these errors to at most 2.3 nanometres.
After fitting, maximum track error is 3.4 nanometres and fractional gyro-gain error
is at most 2.8 × 10⁻⁸. These noise-free controls measure agreement between calculations,
not achievable GPS accuracy.

The calibration problem remains sensitive to small errors. Local condition numbers
are about 11–14 million without roll and 0.70–0.92 million in the second construction.
Good noise-free recovery does not establish reliable recovery with real noise or
the archive's full nuisance freedom.

## Applying the correction twice is wrong

Six additional controls construct precisely defined already-compensated increments
from analytic attitude endpoints and independently integrated force. Original
integration predicts their endpoint positions within floating-point resolution.
Applying the correction again introduces about 41–42 micrometres of error.
The appropriate treatment depends on what each measurement represents.

The software rejects enabled compensation for correctly labelled already-compensated
input. A deliberately false label is used and recorded only to demonstrate the error.
This mathematical convention does not identify Applanix firmware behavior. Endpoint
checks also do not define interpolation within a compensated measurement.

## What follows

The correction passes a wider numerical qualification. It has not established the
NASA calibration-boundary cause, selected an Earth model or calibrated a detection.
The original solver and physical limits were retained. Each model received its own
independently generated observations; this is not a comparison of competing models
against one real recording.

See the [complete report](README.md), [frozen plan](PLAN.md) and
[proposed six-fit NASA comparison](OBSERVED_PLAN.md). The run used 24 starts,
36 known-calibration predictions and 1,042 native sweeps within its 4,836-sweep limit,
with two numerical threads and no retries. All 38 initial focused tests passed.
The [full-column derivative check](DERIVATIVES.md) also passed for all three
candidates, bringing focused verification to 41 passed tests. It verifies local
derivatives with all 27 parameters released, without running a full-parameter fit.
