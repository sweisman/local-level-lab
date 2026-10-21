# Native qualification with the rounded source installed

The physical and trained-source components have passed their separate six-source
qualifications. Local integration checks pass all six model/processing cases,
preserving reference centers, coefficient matrices and all 51 parameter columns.
This new study runs the original full native control matrix.

The candidate replaces only the first-sample force-departure bound with the
qualified source factorization. It advances the source streams once per packet,
reuses each midpoint for both world-step estimates, retains later force
differences, and adds the exact numerical recentering difference to its allowance.
No physical model, calibration domain, reference row, common-error coefficient
or earlier result changes.

## Acceptance and finite work

Reuse all 24 original generated native inputs and original acceptance criteria:
1 micrometre for reference/stationary position, a 0.002 normalized derivative
step with 20 micrometres tolerance, and 10 micrometres numerical allowance for
nonlinear containment. Every control must complete and pass.

- 24 identities, no retries or optimizer starts.
- At most 78 full native evaluations and 19,632 native packet visits.
- At most 348 complete enclosure bounds.
- At most 30,144 bound steps: 15,072 original world steps plus 15,072 physical
  midpoint/end source steps.
- Separately reserve at most 348 source setups, 7,536 compiled source-reference
  steps and 7,536 rounded body bounds before the corresponding enclosure runs.
- Four single-thread workers; four total numerical threads.
- 60 seconds per bound, checked cooperatively; 600 seconds overall.

Freeze source/input/environment/compiler identities. Compile the source-reference
kernel and bound arithmetic from frozen inputs; preserve all reservations and
failures. Full trajectory evaluations and source-only steps are distinct charges.
No aircraft observations or protected ESA records enter this qualification.

Passing permits a separately frozen prediction comparison. It does not establish
useful complete error ranges, whole-program floating-point enclosure, calibrated
observational coverage or a scientific detection.

[Qualified source transfer](../ilvis0-rounded-source-controls/INTERPRETATION.md) ·
[Original native controls](../ilvis0-transform-native-controls/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
