# Known-motion error control

Before estimating prediction error from the recorded ESA flight, the method
needs tests where the aircraft motion and each source of measurement error are
known separately. The software control in
`analysis/lll/esa_motion_error_controls.py` supplies such data without reading
an aircraft recording.

It describes a local north/east/up path moving north at about 80 m/s, with a
small analytic course change and vertical motion. Its separate body attitude
includes slow pitch and optional 10 Hz pitch and forward vibration. Direct
formulas give position, velocity, acceleration, gyroscope rate and specific
force. The sampled IMU output is angle and velocity **increments**; receiver
positions are sampled once per second. The control also retains the true
motion and every error component.

Independent random streams add white gyro and accelerometer error, changing
biases, a correlated gyro/accelerometer error and receiver error. With the same
seed, turning physical vibration off changes the true motion while preserving
the error draws. This creates a matched test of motion/error attribution. Its
numbers are declared software inputs, **not measured ESA instrument limits**.

Three deterministic checks pass. They verify analytic acceleration against
an independent derivative calculation, body gyro rate against an
independently differentiated orientation matrix, force-axis signs, exact
increment conversion, component accounting, separate seeded streams and input
rejection. Run them with:

`~/venv/bin/python -m pytest -q analysis/tests/test_esa_motion_error_controls.py`

The [matched multi-scale result](MOTION_ERROR_CONTRAST.json) uses 120 seconds
at 300 Hz and the existing three-point rate-contrast calculation. It retains
the contribution of each known component, rather than trying to infer it
from the combined stream. All components reconstruct the combined rate to
within 1.8 × 10⁻¹⁵ in native units.

| Span | Combined gyro Y contrast divided by known white gyro contrast | Combined gyro Y / force X correlation |
|---|---:|---:|
| 0.0067 s | 4.6 | −0.004 |
| 0.0200 s | 35.2 | −0.953 |
| 0.2000 s | 2.3 | +0.811 |
| 2.0000 s | 2.7 | +0.858 |

At 0.02 seconds, treating all the observed change as white gyro noise would
overstate the known white component by **35 times**. At 0.2 and 2 seconds,
this control's 10 Hz vibration nearly cancels in the contrast, while the
correlated sensor-error component remains. Thus neither a short-span
variance nor the sign of one cross-axis correlation identifies the physical
source by itself. These ratios belong to this generated example; they are
not estimates for the recorded aircraft.

Reproduce the comparison with
`~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_motion_error_contrast --output docs/prediction-observed-development/MOTION_ERROR_CONTRAST.json`.
Its two focused tests pass with
`~/venv/bin/python -m pytest -q analysis/tests/test_esa_motion_error_contrast.py`.

This establishes a known-truth test input. It has not yet tested a fitted
error law, prediction range or coverage. The next gate is to make a candidate
method predict unused receiver positions in generated controls with changing
motion and error, then apply a separately frozen version to the earlier-only
part of ESA development recording 187. The seven reserved ESA flight groups
remain closed.
