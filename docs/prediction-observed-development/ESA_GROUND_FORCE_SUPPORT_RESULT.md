# Two ground stops add little leverage on aircraft drift

The mean accelerometer vectors from the two ground stops in ESA
recording 187 were only 1.65° apart. Each stop supplies a force
magnitude at a different site. With both site magnitudes unknown,
the two averages alone give no absolute accelerometer calibration.

| Stop | Complete minutes | Mean vector magnitude, m/s² | Range of minute vector magnitudes, m/s² | Mean instrument temperature |
| --- | ---: | ---: | ---: | ---: |
| First | 45 | 9.822013 | 9.821625–9.822237 | 35.78 °C |
| Second | 30 | 9.823074 | 9.822962–9.823126 | 38.37 °C |

The mean magnitudes differ by 0.001061 m/s². That combines possible
local gravity differences, airframe motion and instrument effects.
The recording does not separate those contributions. The second
calibration direction is only about 0.64–0.66% as strong as the first
in the archived normalized parameter coordinates.

Even if the corrected magnitudes were known exactly and the stops
shared one calibration with the airborne interval, only 0.454–0.463%
of the whitened steady-acceleration pattern would survive local flight
calibration. Without those two exact constraints, 0.415–0.424% survives.
All three Earth models gave similar results at both declared rank
tolerances. These are design comparisons using a hypothetical exact
constraint on each magnitude, not measurements of how much the aircraft
drifted.

The replay decoded 1,365,154 samples from the two archived receiver-only
selections and confirmed their timestamps are outside the airborne
training interval. It compared exactly two constraints per model and
ran zero trajectory fits. These stops remain useful checks of motion
and logged variability. For calibration, the next test needs forces
that vary in direction or magnitude and a comparison with receiver-only
acceleration that accounts for its uncertainty.

[Plan and reproduction](ESA_GROUND_FORCE_SUPPORT_PLAN.md) ·
[Frozen inputs](esa-ground-force-support-freeze.json) ·
[Detailed results](esa-ground-force-support-result.json)
