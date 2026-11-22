# Compare force magnitude on the same ESA flight windows

Use the eight previously sealed direction windows from the opened ESA
flight. Compare acceleration magnitude from iMAR with the GIRAFE
recording's atom vertical and two quartz horizontal channels. Magnitude
avoids borrowing fused attitude. It treats the three GIRAFE readings
as a simultaneous orthogonal triad, as a working interpretation of
the file header. This does not qualify the instrument's filter delay,
platform behavior or independent accuracy.

Use the 16 original acceleration supports per window and both the
11- and 25-report kernels. Average the instantaneous force magnitudes
through each kernel. Use iMAR's existing packet intervals and put each
10 Hz GIRAFE observation halfway between its two neighboring sample
edges. Require complete support and reject gaps larger than 0.15 s.
Keep the original UTC conversion as the primary alignment. Replay
four declared shifts of −0.50, −0.10, +0.10 and +0.50 s as sensitivity
checks. No lag, bias or gain is fitted.

Compare the raw iMAR magnitude and its magnitude shifted to the
GIRAFE location with the measured rigid-body correction. The published
offsets imply an iMAR-to-GIRAFE displacement of
\((-0.60,+0.12,-0.48)\) metres in aircraft axes. Treat both estimates as
fixed and neglect changes to the lever arm from platform motion.
[Campaign Table 1](https://essd.copernicus.org/articles/17/1667/2025/#section2)

Report mean, RMS and centered RMS of the sensor difference on the
first eight and last eight supports separately. Keep the individual
measured values, the correction and the interrogation-time range
visible. This compares two sensor channels on one flight. Disagreement
can include errors in either channel, clock and location effects,
and motion of the GIRAFE platform. It neither selects an Earth model
nor determines an independent-flight error allowance.

Freeze eight tasks with one pass of at most 121,000 iMAR intervals per
window, one numerical thread and a 150-second wall limit. Use the
already verified GIRAFE file and the closed iMAR packet windows. Keep
previous forecast holdouts and all reserved flights closed.
