# Receiver-selected development groups for prediction transfer

## Question

Can an earlier-only prediction error rule transfer across conservative flight
groups? The three-recording rolling-origin check found no single useful error
multiplier. This preparation fixes four additional NASA development recordings
using only saved eligibility, trajectory and provenance metadata. It makes no
new model fit or uncertainty claim.

## Selection rule

Start with the unchanged 53 eligible stretches. Verify filename and source hash
against the saved provenance ledger. Exclude all three groups used by the
original prediction pilot. Retain at most one recording from each remaining
group. Choose, in order:

1. The longest remaining southern IMU8 stretch.
2. The longest remaining northern IMU21 stretch.
3. The longest remaining southern IMU21 stretch dated before 2011 from a new group.
4. The longest remaining southern IMU21 stretch dated 2015 or later from a new group.

Break duration ties by segment ID. All four categories must be populated.
Use only the published segment ID, filename, source hash, start/end time,
duration, IMU type, mean latitude/course and ground-speed summaries. The
outcome fields, gyro values and model residuals cannot enter selection.
These groups are conservative split units, not proven independent aircraft or
instrument installations. The NASA archive has already informed development;
this is retrospective transfer testing, not protected confirmation.

For each selected recording, the first `floor(2N/3)` receiver epochs form the
outer training prefix and the rest form later scoring epochs. The saved
[split receipt](split-receipt.json) fixes the exact times without reading
receiver position values or gyro values. A later rolling-origin comparison may
also use the first `floor(N/3)` epochs as an earlier training prefix, but must
freeze its equal-horizon scoring rule before fitting.

## Later finite gate

Selection alone does not authorize fits. Before a separate observed run, freeze
the exact use of the earlier/later cuts, training-only error-law estimator, model/clock/
processing grid, starts, stopping rules, physical adequacy screen, source and
environment hashes, finite charges, recovery procedure and group-level scoring.
Preserve all failures. A later rule may not be chosen using withheld positions.
The seven reserved ESA confirmation groups stay closed.

[Prediction protocol](../PREDICTION_VALIDATION.md) ·
[Rolling-origin finding](../prediction-rolling-origin/INTERPRETATION.md)
