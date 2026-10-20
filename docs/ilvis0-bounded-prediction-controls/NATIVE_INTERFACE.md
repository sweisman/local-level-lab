# Training-only prediction interface controls

Seventeen component tests pass for the new interface between supplied native
predictions/derivatives and the qualified structured uncertainty calculation.
It performs no integration, fitting or archive reads.

The checks cover a nonzero fitted center, complete four- and 27-parameter boxes,
unidentified directions, affine coordinate transformations, a two-member
covariance family and an independently bounded quadratic mean error. They also
check that a bad candidate cannot enlarge the shared scale, a missing covariance
alternative cannot disappear, and a bound cannot be reused for another model,
center, box, parameter order or numerical error configuration.

Future observations are absent from the API. Coordinate transforms are frozen
configuration; the interface neither recalculates them from withheld positions
nor silently wraps longitude. Native Jacobians use the full training-noise
dimension. Missing global approximation bounds produce unsupported envelopes;
sampled local probes are not accepted as a global-bound declaration.

This qualifies interface calculations on supplied mathematical inputs. It does
not establish a global native remainder bound, qualify the source of the native
predictions, or calibrate the receiver-error family on aircraft observations.
Every output remains a scientific abstention, including supported mathematical
envelopes. These gates remain ahead of a new observed prediction study.

Implementation: `lll.ilvis0_prediction_envelope_adapter`.
Checks: `analysis/tests/test_ilvis0_prediction_envelope_adapter.py`.

[Interface design](NATIVE_INTERFACE_PLAN.md) · [Mathematics](MATHEMATICS.md) ·
[Native source audit](NATIVE_AUDIT.md) · [Next gates](NEXT_PLAN.md).
