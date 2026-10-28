# Timing and rounding: small known-answer controls

The completed stopping diagnostic found two different patterns: a timing
derivative discrepancy that persists as the test step shrinks, and a weak gyro
offset discrepancy that grows. This follow-up tests possible explanations
without changing the solver or repeating calibration.

## Fixed questions and work

| Control | Cases | Independent check |
|---|---:|---|
| Constant vertical acceleration | 3 | Exact quadratic position and linear velocity, at an interior time and a packet boundary, including a bounded time offset |
| Turning sensor with constant body-frame force | 2 | Closed-form derivatives of the midpoint packet calculation on either side of a boundary |
| Weak gyro offset | 2 | The same motion with longitude origins of zero and one radian; an independent polynomial gives the leading derivative |

The second control distinguishes a derivative within one packet from the
derivative approached through the next packet. It also reports the continuous
motion solution separately: agreement with a discrete calculation is not proof
of its physical accuracy. The third changes only a coordinate origin, not the
physical trajectory, to expose loss of small changes beside a large coordinate.

## Implementation and limits

Add `analysis/lll/timing_precision_controls.py` for the cases, independent
references and a small `lll.studies` adapter. Add focused tests in
`analysis/tests/test_timing_precision_controls.py`. Reuse the existing native
source, wider loader, study engine and source/compiler-bound build cache.
The frozen wider implementation stays unchanged.

Run the tests first, then freeze seven controls with one worker and one numerical
thread, zero reserved threads, at most eight native evaluations per case and
one source/compiler-bound build. Allow ten minutes cooperatively. Charge calls
before execution; preserve failures. No optimizer starts, noise draws, aircraft
reads, protected inputs, new uncertainty thresholds or changed fit labels.

Publish all seven outcomes, the exact source/environment binding and the
remaining explanation gap. These small controls may isolate a mechanism;
they cannot establish that it explains the four saved calibration points.
A further saved-point comparison would need its own finite freeze.
