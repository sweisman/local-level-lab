# Testing predictions on unused measurements

The next milestone is a direct test: calibrate each model on the earlier part
of a recording, then reconstruct the later flight from its **IMU (inertial
measurement unit)** readings. Keep later GPS positions out of calibration and
use them only to measure prediction error. The path must continue across the
split without a GPS reset.

This is a revised development protocol. It replaces the requirement to finish
global interval certification before making another exploratory aircraft
prediction comparison. Earlier studies, limits and failure labels remain
unchanged. Formal uncertainty certification remains a separate research track;
the production evidence gate and requirements for significance stay intact.

## The sequence

| Step | Work | Required result |
|---|---|---|
| V01: software qualification | Reuse the shared motion, solver and prediction code. Check all three candidates, both processing assumptions, clock treatment and all active calibration parameters on known-answer controls. | Correct units and frames; training-only initialization, fitting and error-model choices; repeatable objectives and predictions; explicit failures. |
| V02: small archival pilot | Select a small representative set using route, completeness, IMU type and conservative flight-group metadata. Freeze the selection, split, starts, numerical limits and scoring rules before new fits. | Complete earlier/later error curves, including height, and results from every planned start. |
| Replication | Apply the qualified fixed procedure to additional distinct groups. Keep overlapping recorders together when summarizing evidence. | Report repeatability and failures across groups, without counting stretches as independent flights. |
| Uncertainty and detection | Test the complete fitting/prediction procedure under declared correlated-error scenarios; assess the observation-error model and calibrate the two-stage decision. | Only qualified procedures may produce calibrated intervals, detection thresholds or significance claims. |

## What stays fixed

- Use the original measurements and saved eligible stretches. Select no new
  interval because its gyro residual or model preference looks favorable.
- Fit all three candidates under the same declared physical calibration bounds
  and matched processing/error assumptions. Do not use fused navigation as an
  independent measurement or transfer proprietary device claims into measured bounds.
- Use a contiguous earlier training block and later prediction block. Set their
  exact UTC boundaries before fitting. Keep later positions out of initialization,
  covariance selection, starting-point selection and calibration corrections.
- Choose starts in advance. Select the reported primary using training cost
  only, with a fixed tie rule; preserve every start, failure and alternative.
- Treat disagreement between later predictions as sensitivity, not an automatic
  optimizer failure. A spread across a few starts is not a confidence interval
  or a complete bound on calibration uncertainty.
- Report north, east and height errors, horizontal and three-dimensional RMS,
  largest errors, time trends and temporal correlation. Excellent horizontal
  agreement cannot compensate for an implausible altitude reconstruction.
- Interpret globe versus the specified disc first. Compare specified-field and
  zero-field globe predictions only after the required shape comparisons finish.

## What a result can establish

Numerical convergence, prediction accuracy, physical adequacy and calibrated
confidence are separate results. Report an unfinished fit as unfinished. Report
a lower error as a relative advantage. Call an absolute adequacy criterion
calibrated only after its observation-error assumptions and coverage are tested.
Fix any descriptive accuracy thresholds before evaluation and label them accordingly.

The NASA recordings have already informed development. New splits can test
training-only prediction, but they remain retrospective development validation.
Reserved ESA groups remain untouched until the independent-confirmation method
is frozen.

The [existing saved-data check](ilvis0-saved-prediction-comparison/INTERPRETATION.md)
already shows a substantial later horizontal-error advantage on one recording.
The next purpose is to test whether that result repeats across different groups
and remains stable under the declared assumptions.

## Implementation and execution

Reuse `lll.ilvis0_prediction` for split and initialization safeguards, the qualified
native motion and solver libraries, `lll.ilvis0_forecast` for observation-free
propagation, and `lll.studies` for freezes, charges, locks,
atomic outputs and publication. Extract reusable code from historical workers
when needed; do not copy a worker tree or alter its frozen source.

The observation-free native forecast adapter passes 29 focused checks. These
cover all three candidates, both processing assumptions and both clocks, preserve
all active derivative columns, and reject a changed training prefix before
charging a native call. This component has no later receiver-position or
covariance input. It does not yet qualify the complete fitting/prediction pipeline.

Next verify initialization, training-only fitting and start-to-start behavior
together on known-answer controls. Then publish a metadata-selected pilot inventory and a finite costed
definition. No observed start is charged before the relevant software checks
and new source/input/environment freeze are complete. Preserve the four-thread
total limit and every charged failure. A completed allowance cannot be reused.

The completed [training-bound study](ilvis0-dense-physical-bounds/INTERPRETATION.md)
preserved 348 reports; all six cases stopped at a square-root-domain check.
None qualified. Its failures remain published, and no further interval-bound
expansion is part of this revised immediate sequence.
The old [global-bound requirements](ilvis0-long-staged-feasibility-v2/V01_GATES.md)
remain the requirements for that separate research method, not a claim that it
has qualified.

[Roadmap](ANALYSIS_ROADMAP.md) · [Next steps](NEXT_STEPS.md) ·
[Error assumptions](PREDICTION_ERROR_ASSUMPTIONS.md) · [Study history](STUDIES.md)
