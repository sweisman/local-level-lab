# ESA geographic adapter: implementation sequence

Use the [scientific plan](PLAN.md) and the approved roadmap. This is a generated
software qualification; it consumes no observed-data allowance.

## Shared implementation

Keep the independent geometry in `analysis/lll/airquantumgrav_truth.py`, which
imports no navigation or model library. Its `truth(model, times, *, latitude_deg,
pattern, removal)` interface returns the analytic channels listed below.
`analysis/lll/airquantumgrav_geographic_controls.py` is the small study adapter, with:

- `recipe()` returning the complete analytic parameters, accuracy checks and
  finite limits. The final numeric recipe must be fixed before execution.
- `truth(model, times, *, latitude_deg, pattern, removal)` in the independent
  geometry module, returning analytic
  coordinates, coordinate derivatives, body-to-local rotations, gyro rates,
  specific force and true initial state. Derive these from Cartesian geometry,
  without importing the native predictor, coordinate/transport helpers or
  `lll.models`.
- `construct(case, *, method, rate_hz, reserve, chunk_size=4096)` streaming through the existing
  `IntervalStream`, retaining actual timestamps and explicit sampling semantics.
- `evaluate(task, context)` charging construction and native calls before work,
  running the unchanged native kernel twice, and saving complete error curves.
- `prepare(root, *, qualification, identity=...)` checking the source-bound derivative/loader qualification,
  resolving explicit compiled dependencies, and using `lll.studies` for freezing.

Reuse the existing numerical kernel, rate adapter, artifact store, journal,
locks and publication machinery. Do not copy a historical worker or introduce
a second navigation solver. Report generation reads saved results only.

Use a shared `lll.studies.qualification` component for the pre-test source and
environment binding. `request(root, *, sources, environment, output, report)`
must refuse an existing request or report. `checked(root, request_path, *,
sources, environment, required_tests, minimum_tests)` must reject changed
source/environment bindings, failed or skipped tests, missing required tests
and insufficient actual cases. It returns the exact request/report bytes for
the study freeze. Its tests use small metadata fixtures, with no numerical
library import or additional numerical allocation.

## Verification order

Completed execution: all 40 focused checks pass, including independent geometry,
native short trajectories, input rejection, accounting and isolated compilation.
The exact source/environment request and test report have been verified and
included in the freeze. The separately budgeted [72-case study](README.md)
passed all checks in 31.29 minutes, using 144 native propagations. Linear point
samples meet the accuracy screen; hold rules meet refinement requirements but
have large absolute errors. Saved-only verification checks hashes, error curves,
shared input hashes and both accounting journals. No observed ESA fit ran.

1. Add generator tests in `analysis/tests/test_airquantumgrav_geographic_controls.py`
   and adapter tests in `analysis/tests/test_airquantumgrav_geographic_study.py`. Observe the
   new API tests fail before implementation. Keep numerical tests queued while
   the NASA pilot occupies the four-thread allocation.
2. Check generator derivatives independently; cover the three models, both
   latitude signs, changing attitude, zero motion and common field removal.
   Check that the generator cannot import the code under test.
3. Check actual adapter chunk equivalence and failure on a gap, reversed time,
   malformed input or an undeclared sampling hypothesis. Verify that generated
   component increments are never labeled instrument increments.
4. Check native calls and interval counts against an independent charge callback.
   Test malformed recipes and limits before work. Compile from an isolated
   declared source snapshot, including both native translation units.
5. After the numerical allocation is free, run these focused tests through
   `analysis/tests/run_numerical.py`. Freeze the exact tested source and
   environment, recipe and 72 identities. Register the study in
   `analysis/study-status.json`, then run the finite definition.
6. Verify every saved result and charge before publication. Update the roadmap,
   study index and ESA overview with the actual outcome and next gate. Preserve
   failures, the existing zero-eligible inventory and all confirmation reservations.

## Release boundaries

The [known-correction extension](../esa-observation-controls/README.md) now passes
all 24 cases with nonzero antenna offsets and supplied initial-state and sensor
corrections. The [next check](../esa-training-forecast-controls/PLAN.md) estimates
unknown calibration from earlier observations. Receiver-error assessment and a
new selection freeze follow before any observed ESA fit. These results do not
establish the instrument's actual sample averaging or phase.

The new tests do not alter an active NASA freeze. Generated accuracy and
refinement checks do not calibrate receiver or inertial errors. A passing
calculation is a prerequisite for revising ESA selection, not permission to
fit protected recordings. Nonzero lever arms and uncertain initialization
need their own explicit qualification before the observed adapter is complete.
