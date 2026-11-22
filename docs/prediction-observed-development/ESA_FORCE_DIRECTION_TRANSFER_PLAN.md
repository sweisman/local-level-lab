# Predict force directions after aligning on earlier vectors

Use the same 16 force supports from the opened ESA development flight.
Express the logged accelerometer vectors in a common frame using the
logged gyroscope increments. Separately compute the force directions
required by the existing globe and disc models. Use the three sealed
velocity sources and both averaging widths. Use no fused attitude.

For each shape, estimate one proper three-dimensional rotation using only
the first eight unit force vectors. Apply that same rotation to predict
the last eight directions. Report the angular RMS for the alignment
interval and the forecast interval. Report the smallest to largest
rotational information eigenvalue ratio on the first eight vectors and
abstain when it is at most 10⁻¹⁰. This guard excludes a numerically free
rotation about the common force axis. It gives no physical uncertainty bound.

Compare shape within each matched field setting. Use a zero field for
both candidates, and the same specified geographic field in both force
equations with the zero and full retained-rate endpoints. Apply the same
isolated X accelerometer bias to both candidates, separately at −0.10,
0, +0.0225, +0.05 and +0.10 m/s². Do not select or optimize a bias or
field setting against the later vectors. Preserve every result.

One task permits at most 180 analytic alignments and 119,865 used gyro
intervals, on one numerical thread and within a 90-second wall limit.
Check the nominal eight pair angles against the published directions.
Use only the first 400 receiver reports of the original cut, including
the eight later evaluation supports within those reports. Do not open
the original forecast's later 120 positions or any reserved flight.
This direction test is a descriptive development result. It does not
isolate the gyro from its gain, bias, processing or motion uncertainty.
