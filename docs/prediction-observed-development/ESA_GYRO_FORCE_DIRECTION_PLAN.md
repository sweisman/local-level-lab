# Use the gyroscope to compare changes in force direction

Use the same sealed first 400 reports, 16 centers, 11- and 25-report
stencils, three velocity sources and matched acceleration weights as
the force-magnitude check. Use its fixed working gravity of 9.81 m/s².
For each inertial interval, use the logged incremental angle to express
the force vector in the starting sensor frame. Use midpoint rotation
within each interval. Average vectors with the same time kernel as
the receiver calculation.

Use the candidate path and force equations to predict the mean force
vector in the corresponding common spatial frame. Compare the angles
between windows eight blocks apart. No starting attitude is needed,
since a common rotation of all force vectors leaves those angles
unchanged. The eight pair separations are about 200 seconds. Report
all pairs and receiver/stencil cases.

Use the specified-field globe, still globe and still disc. For the
specified-field globe compare two cases. If the logged gyro retains
the field, use the frame that includes the specified sidereal rotation.
If the gyro has already had that full field removed, compare in the
Earth-fixed globe frame. The force equations still include the
specified field in both cases. There is no assumed gyro calibration
correction, estimated heading, fitted rotation, or optimized time lag.
The artificial matched-field disc from the scalar experiment has no
declared common inertial frame, so the directional experiment uses its
three original candidates.

Test exact angular differences and noncommuting gyro increments before
running. Freeze one thread, at most 155,868 intervals and 288
candidate vector averages, with 96 extra frame transformations for
the second specified-field case. Use no new Earth-model fits or later
120 reports. The seven reserved groups stay closed. The result is
descriptive. It does not calibrate gyro bias, receiver error or a
flight-level decision.

[Force-magnitude check](ESA_DOPPLER_FORCE_RESULT.md)
