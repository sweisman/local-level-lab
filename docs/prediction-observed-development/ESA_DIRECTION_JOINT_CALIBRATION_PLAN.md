# Test gyro and accelerometer calibration together

Use all 18 matched ESA settings and the same earlier and later force
supports. Fit all six gyro biases and gains and all six accelerometer
biases and gains in the existing working boxes. Reuse the earlier-only
starting-frame fit. The three starts are zero and opposite half-box
perturbations. Do not choose a field assumption using the later directions.

Build a local approximation to the gyro-dependent force averages from
the nominal increments and two exact packet integrations per gyro
coordinate, at ±0.02 normalized units. The bounded search can use this
approximation for up to 200 earlier objective calls per start. Replay
the selected calibration from every start using the exact corrected
gyro increments and exact accelerometer averages. Recompute the
starting rotation on the earlier directions of each replay.

Require the predefined projected-gradient limit of 10⁻¹⁰ for the search
and an earlier RMS discrepancy of at most 0.0001 in unit-vector chord
distance between the search approximation and exact packet replay.
Choose the primary start by exact earlier chord loss among points
passing those checks, then compare exact later angles. This tests an
explicit calibrated point. It does not certify the nonlinear global
optimum, exact stationarity after packet replay, or the full calibration
envelope. Preserve numerical failures, later discrepancies and all
starts separately. Keep relative gain scale information separate from
physical calibration claims.

Freeze at most 121 packet passes of 119,865 intervals and 108 starts on
one numerical thread with a 90-second wall limit. No full inertial fit
or independent-flight data is used. The seven reserved groups and the
120 original position-forecast observations stay outside the comparison.
