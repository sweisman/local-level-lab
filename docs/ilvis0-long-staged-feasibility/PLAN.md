# Full-history training and prediction feasibility

## Question

Can earlier position observations make a later prediction usefully narrow over
a recording-length history, without discarding calibration directions?

This is a generated-data development test. It uses no aircraft observations,
protected ESA outcomes or optimizer starts. It cannot establish aircraft error
coverage or qualify a physical model merely by containing its generated truth.

## Fixed calculation

- Six cases: all three physical candidates, each with zero and profiled removal.
- Use the six qualified 96,000-packet, eight-minute inputs unchanged. Their first
  four minutes match the earlier inputs bit for bit. Preserve all 27 physical
  directions and the original broad bounds; the clock range is ±1 second.
- Use the same frozen initial coordinate-to-metre factors for every candidate.
  These define a fixed comparison frame, not a new independent position source.
- Training times: 2, 10, 30, 180 and 290 seconds. The first three form stage one;
  the last two form stage two. Retain every earlier inequality and the same
  calibration reference, including all 24 shared expression coordinates.
- Five necessary training constraints are deliberately a conservative subset of
  the earlier 292-epoch training period. This is not a fit to all 292 epochs.
  No training observation occurs after that earlier plan's 291-second cutoff.
- The known normalized calibration vector is 0.05 × (axis-index modulo 3 − 1),
  except clock coordinate 25, which is +0.25. It is identical across cases.
- Add the fixed coordinate-error pattern 0.25 × ((epoch-index + 2 × axis-index)
  modulo 3 − 1) metres. Allow ±1 metre on each training coordinate. This is a
  software assumption, not an instrument specification or a Gaussian error law.
- Predict at 438 seconds. Do not construct or inspect future truth until the
  prediction and its exact support certificates have been saved.
- Require exact retention of the known training witness, containment of future
  truth, preserved warning/status metadata, independent support/endpoint checks
  and all earlier rows. Any native warning fails this qualification.
- The engineering usefulness target is total width ≤20 m north, ≤20 m east and
  ≤50 m height in every case. These are preregistered development thresholds,
  not scientific detection or aircraft adequacy limits. Wide ranges fail even
  if they contain the truth. Do not widen the target after seeing results.

## Finite allowance

| Work | Per case | Six-case maximum |
|---|---:|---:|
| Native value/Jacobian queries | 12 | 72 |
| Conservatively charged native packet visits | 1,152,000 | 6,912,000 |
| Source bounds | 6 | 36 |
| Logical bound steps (nine full streams per bound) | 5,184,000 | 31,104,000 |
| Training-conditioning LP proposals | 18 | 108 |
| Exact support checks | 66 | 396 |

Each bound additionally reserves its full 96,000-packet source, derivative,
point and direct streams before execution; unused reservations remain charged.
Reserve one reference, one physical proof, two conditioning proofs and one
post-prediction truth audit per case. All auxiliary reservations are journaled.

Use two workers, one numerical thread each, for two total threads. Freeze the
runtime/source/input environment and use disk scratch. Based on the measured
50-second costs, expect roughly 6–8 wall hours, with a finite 14-hour cooperative
study ceiling and two hours per bound. These limits stop new work cooperatively;
they do not authorize process termination, retries or enlargement.

Retain failed/unfinished cases, original charged identities and every earlier
study. Each query has its own bound; no unqualified multi-time bound reuse.
The small staged controls and duration adapter must pass before preparation.
Packaging checks sealed evidence only and never repeats numerical work.

## Interpretation

Even a complete pass qualifies only this stated recording-length, fixed-error
generated test at the declared future endpoint. It does not certify every later
epoch, combined stochastic IMU/GPS errors, independent physical truth or a
whole-program floating-point enclosure. Those V01 requirements remain open.
Failure is evidence about this method; it is not permission to narrow physical
bounds, discard directions, retry identities or begin V02 observed fits.

[Roadmap](../ANALYSIS_ROADMAP.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md)
