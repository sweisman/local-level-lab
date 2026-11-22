# Next generated qualification: a realistic forecast gate

The eight-case cohort remains a failed test under its original coded rule.
Its [saved noise-floor audit](GENERATED_NOISE_FLOOR_AUDIT_RESULT.md) shows why
the inherited 0.1 m deterministic path screen is unsuitable for a noisy IMU:
the declared fixed-calibration forecast noise alone has a 17.39 m horizontal
RMS second-moment scale. The next study needs a **new source and identity**;
it must not relabel or rerun any completed task.

## Fix the question before running

1. Keep **two explicit targets**. Generated controls can check the true
   later physical position without receiver noise. An aircraft check scores
   later receiver measurements, so its predictive range must also include
   later receiver error. Fit earlier receiver data and IMU only. Save the
   point forecast, conditional center and both target-specific uncertainty
   envelopes before opening later generated truth or aircraft observations.
2. Report numerical convergence, training residual adequacy, future point
   error, future uncertainty containment and interval width **separately**.
   A point path may miss the true path under the declared noise even when
   the predictive distribution is adequate. Wide ranges that contain every
   candidate carry little model-discrimination information.
3. Retain all calibration directions and the same physical parameter box.
   Test nonlinear calibration effects and fit boundaries; the current
   affine Gaussian envelope is a software candidate, not established
   nonlinear coverage. Do not treat the known generating calibration as an
   input to the actual estimator.
4. Use distinct generated route geometries and fresh noise seeds. Keep
   method selection/development cases separate from a source-frozen
   confirmation cohort. Include every numerical or interval failure in the
   confirmation denominator. Use the existing exact binomial planner for
   the chosen failure-rate claim; eight same-route cases cannot establish it.
5. Record a width or model-separation requirement **before** confirmation.
   Otherwise arbitrarily broad intervals could pass coverage while the
   experiment cannot distinguish the candidate models.
6. Repeat across plausible correlated noise, bias drift, receiver error and
   preprocessing cases. Generated coverage under a supplied law does not
   establish that law for the opened ESA aircraft, and reserved ESA groups
   remain closed until the complete rule and observed error assumptions are
   fixed.

Implementation should reuse `lll.studies`, `lll.prediction_calibration`,
`lll.bounded_forecast_wrapper` and the shared forecast/score functions.
The existing `test_native_error_extension.py` checks that the forecast
operator retains future receiver error only for the receiver-measurement
target (10 local checks pass). Its target-covariance control confirms that
correlated receiver states can make some horizontal variances slightly
smaller even as vertical uncertainty grows; the two targets must not be
compared by assuming every variance increases. This is a component check,
not a complete two-target fitted-forecast qualification.
Qualify a short source-bound preflight and task-level recovery before a
finite full campaign. Freeze route identities, seeds, worker/thread counts,
evaluation and wall limits, source/environment hashes and all acceptance
metrics. Keep the total numerical allocation at or below four threads.

The first step is a software control for the proposed **metric and width
rule**, not another large fitted cohort. Its test must show that the rule
recognizes a narrow known-answer forecast and abstains for an
uninformative but very wide forecast. Only then should a full campaign be
costed and frozen.
That [deterministic control](FORECAST_ENVELOPE_CONTROL.md) now passes six
checks. It reports only descriptive containment and always abstains from a
scientific decision. The [dual-target generated pilot](DUAL_TARGET_GENERATED_PILOT_PLAN.md)
has passed its 1/1 short source-bound **wiring** preflight: both
physical-position and receiver-measurement bounds were sealed before later
truth was scored. The deliberately short fit did not converge. A
separate generated receiver replay reproduced the earlier noise prefix and
placed all 9 later preflight coordinates within the saved receiver bounds;
the mean full horizontal width was 344 m. This checks wiring, not coverage.
The [two full generated fits](DUAL_TARGET_GENERATED_RESULT.md) have now closed:
2/2 technical passes and 2/2 converged fits. All later receiver coordinates
are inside the saved ranges, whose mean full horizontal width is about 208 m.
The raw physical paths still fail the inherited 0.1 m screen. Independent
empirical coverage, useful model separation and an observed-aircraft error
law remain open.
The [matched development matrix](MATCHED_CANDIDATE_GENERATED_RESULT.md)
gave each of twelve generated recordings to all three candidate models.
All 36 fits converged, but every receiver path lay inside every candidate
range, and no pair of ranges separated. These results remain descriptive.
The [saved horizon and width checks](MATCHED_CANDIDATE_GENERATED_RESULT.md)
find that separation stays below the range width and the late width is
dominated by calibration allowance. Diagnose supported calibration directions
before designing another fitted study.
