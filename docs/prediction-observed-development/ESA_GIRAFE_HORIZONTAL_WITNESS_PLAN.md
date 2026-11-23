# Test the north–south error with independent horizontal force

Use only the sealed two-minute ESA development path and its north-only
error construction from the motion-axis check. Use the original 2 Hz
carrier coordinates and recorded times. Add the exact witness shape in
the original coordinate metric. Compare the original and displaced paths
under equal zero background field for the globe and the specified disc.
Retain both physical cases and both paths regardless of the results.

Before reading the force values, fix five support centers at 12, 36, 60,
84 and 108 seconds after GPS 388614. Apply the position-derived acceleration
kernel on 10-second and 24-second supports. Integrate the receiver-derived
force and the recorded quartz horizontal vector with the same kernel.
Use the logged clock and a fixed ±0.1-second sensitivity, with no choice
of best shift. Rectangular measurement time cells are an approximation
to the undocumented quartz response. Report both the magnitude of the
averaged vector and the average of the instantaneous magnitudes, which
check the effect of averaging. Never interpolate the raw forces.

The norm of a horizontal force vector eliminates an unknown constant
heading between north/east and the platform axes. Report the change due
to the witness and the measured-minus-predicted RMS for each case. These
are diagnostics of the current data and assumed level platform. Unknown
tilt, time-varying yaw, transfer response, relative sensor location and
absolute accuracy still prevent using them as a bound or deciding shape.

Use one task and one numerical thread, one scan of at most 50,000 source
rows and ten support calculations, with four fixed candidate paths each
and three declared clock alignments for the measurements. Bind the
original reports, qualification and recovery. Run no new Earth model fits
and read no reserved flight data.
