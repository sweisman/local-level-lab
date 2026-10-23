# Search for distinct training-compatible predictions

The completed six-case bound comparison passes numerical checks but gives no
usefully narrow ranges. This diagnostic asks whether different calibrations
really can fit the same earlier observations while predicting different later
positions. It uses the original generated histories, not aircraft measurements.

## Fixed problem

Keep all three physical candidates and both upstream-processing assumptions.
Preserve the six source files byte for byte, all 27 normalized calibration
coordinates and their original limits, including the ±1-second clock range.
Use the same coordinate frames and scales.

Training uses the stored perturbed positions at 2, 10, 30, 180 and 290 seconds,
with ±1 m coordinate allowances. The prediction is at 438 seconds. Do not
substitute noiseless training positions or consult future observations.
The saved initial calibration is a known-answer starting point for these
software controls; it is not an estimate obtained from aircraft observations.

There are twelve fixed searches: one in each north-coordinate direction for
every model/processing case. Use SLSQP with actual nonlinear native positions
and all 27 Jacobian columns, at most 32 iterations and 32 new native batches.
The search retains a 0.01 m training margin, in addition to a supplied
0.00001 m numerical allowance. This restricts proposals without narrowing the
declared physical domain or changing the original observation problem.

Save and charge every new point before execution. Preserve failed outputs and
all training mismatches. Repeated requests for the same point use cached
outputs. Select the best point that passes the exact training audit, regardless
of the optimizer's success label. Save the selection before one separately
charged final replay; require identical positions and valid packet counters.

## Qualification and finite allowance

Forty-seven focused checks pass before this freeze. They include independent
nonlinear and boundary optima, failure of a misleading linear approximation,
budget exhaustion, all six small native model/processing paths, charge ordering,
input/source mismatch rejection and the runner's standalone loading method.

| Resource | Per identity | Total maximum |
|---|---:|---:|
| Search identities | 1 | 12 |
| Search native batches | 32 | 384 |
| Final verification batches | 1 | 12 |
| All native batches | 33 | 396 |
| Queried epochs | 198 | 2,376 |
| Conservatively charged packet visits | 19,008,000 | 228,096,000 |

Each batch requests the five training epochs and prediction endpoint on the
96,000-packet history. There are no trajectory-enclosure calls or aircraft fits.
Use four one-thread workers, a one-hour cooperative study ceiling and a
30-minute per-identity ceiling. No retries, process signals or allowance expansion.

The shared study runner freezes source, inputs, compiler/environment information
and resource limits. Its immutable journals retain every charged attempt.

## Interpretation

Compare the two replayed calibrations for each case with the exact saved-pair
audit. Check original bounds, training errors and future separation under the
same source/configuration bindings. Retain all twelve outcomes, including failed
searches. A failed direction leaves its comparison incomplete.

Separation beyond 20 m north, 20 m east or 50 m height supplies a lower width
for the represented native calculation, subject to the stated numerical allowance.
That allowance is a test assumption, not a qualified whole-program error bound.
No physical impossibility claim follows without a justified bound and sufficient
margin. A search finding no large separation proves neither uniqueness nor a
useful outer range.

If genuine ambiguity is established, add predeclared training information rather
than tighten calibration assumptions or widen targets. Neither outcome changes
the 53-stretch findings or qualifies aircraft prediction fits.

[Preceding comparison](../ilvis0-long-remainder-feasibility/README.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).
