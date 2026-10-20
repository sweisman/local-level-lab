# A combined error budget for the acceleration-only diagnostic

The deterministic software chain now passes **126 checks**. These include
**15 calibrated-increment checks and six end-to-end examples** joining
independently generated receiver trajectories and integer IMU observations.
They do not analyze new recordings or change the 53-stretch findings.

An **IMU (inertial measurement unit)** records turning and specific force.
This diagnostic deliberately omits turning measurements: it compares the
magnitude of measured specific force with the magnitude needed to follow the
receiver trajectory, under each declared geometry. It is a necessary constraint,
not a full gyro-free navigation solution.

## What is combined

| Component | Checked treatment |
|---|---|
| [Integer resolution and periods](QUANTIZATION.md) | Preserve signed counts; declare count-error boxes and integration-period hypotheses. |
| Calibration | Correct increments as `(delta_v − offset × period) / (1 + gain)`, retaining interval bounds on each axis. |
| [Force-vector averaging](FORCE_AVERAGING.md) | Bound the difference between an integrated vector's magnitude and continuous force magnitude under an explicit direction-rate envelope. |
| [Time support](TIME_SUPPORT.md) | Use whole packets and the same retained interval union; preserve gaps and uncertain boundaries. Bound common latency and prediction averaging separately. |
| [Receiver derivatives](DERIVATIVE_BOUNDS.md) | Carry declared coordinate-error and higher-derivative bounds through all nine trajectory quantities. |
| [Nonlinear force response](FORCE_BOUNDS.md) | Propagate coordinate, rate, acceleration, gravity and field intervals through the candidate's full force calculation. |

The receiver and measured-increment sides then each produce a lower/upper
continuous force-magnitude envelope on the same time support. Statistical
independence is not assumed to shrink any deterministic component.

Calibration intervals are common across the recording. Interval propagation
relaxes the dependence created by sharing those parameters; it can therefore
be conservative. An overlap does **not** prove that one constant calibration
fits the entire history, establish orientation, or identify a complete
gyro-free reconstruction.

## What the comparison reports

- **Overlap:** this necessary scalar constraint does not exclude the candidate.
- **Disjoint:** the envelopes are incompatible under the declared error and
  physical bounds; the minimum deterministic gap is reported.
- **Unsupported:** a required bound is unavailable, such as continuous magnitude
  without a supported force-direction envelope.

Every path still abstains from a scientific decision. These are neither
calibrated confidence levels nor a replacement for the production evidence gate.
An unsupported or overlapping result cannot be converted into a positive finding.

## Independent end-to-end checks

The six examples cover changing-course and climbing motion under all three
candidates. A separate Cartesian generator supplies coordinate truth and force.
The receiver path includes declared coordinate errors. The IMU path integrates
body-frame force, applies a known gain/offset and nonzero latency, then quantizes
to signed integers. Both propagated envelopes contain the generated truth.

The example calibration, motion and clock limits are constructed test inputs,
not measured specifications for Applanix hardware. Checks of their mathematical
propagation do not establish the correct physical allowances for a recording.
Floating-point operations are checked but are not a formal rounding certificate.

## The next observational gate

Freeze a finite, receiver-selected descriptive comparison with named clock,
calibration, motion, coordinate-error and trajectory-truncation hypotheses.
Use the same policy for every candidate, preserve all exclusions and unsupported
intervals, and report sensitivity to those hypotheses. The existing mathematical
calibration matrix remains separate from this conservative envelope calculation.
No recorded-data likelihood or calibrated detection follows automatically.

[Measured-side implementation](../../analysis/lll/ilvis0_calibrated_bounds.py) ·
[Calibration checks](../../analysis/tests/test_ilvis0_calibrated_bounds.py) ·
[End-to-end checks](../../analysis/tests/test_ilvis0_combined_bounds.py) ·
[Contribution overview](README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
