# Time-matched receiver and accelerometer force on one ESA flight

A single force offset did not transfer consistently across three
preselected windows on ESA recording 187. After subtracting the median
offset from the other two windows, the force disagreement was about
0.005–0.007 m/s² RMS in two windows and 0.065 m/s² in the third. Even the
smaller disagreements are several times the 0.001 m/s² steady-drift
scale under study.

| Training window | Median logged force minus receiver force, m/s² | Offset estimated from the other two windows, m/s² | RMS difference after applying that offset, m/s² |
| --- | ---: | ---: | ---: |
| 187-042470-044870 | 0.0231 | 0.0179 | 0.0070 |
| 187-049554-051954 | 0.0183 | 0.0184 | 0.0649 |
| 187-058525-060925 | 0.0161 | 0.0196 | 0.0049 |

The middle window's near-zero median after correction conceals large
individual differences. Several comparisons differ by more than
0.15 m/s² and the largest differs by 0.176 m/s². Those large differences
all occur in the first half of the window, where the [earlier motion
check](ESA_COMPONENT_PREFLIGHT_RESULT.md) found its maneuver exposure.
The last half stays between 0.0169 and 0.0185 m/s² before correction.
All 32 centers per window were retained. For the receiver's smooth path, matching the
averaging changed the median force magnitude by less than 0.00009 m/s²
in each window compared with the center-only estimate.

The same time weights were applied to the magnitude of the logged IMU
acceleration and to the magnitude required by the position-derived
receiver trajectory. The replay verified all 96 receiver centers and
decoded 719,097 raw samples from the earlier portions of the windows.
No heading from fused navigation was used. The receiver side used the
conventional rotating-globe chart and the same fixed apparent gravity
of 9.81 m/s² as the previous check. That convention is separate from a
comparison of Earth models.

This is a descriptive transfer check within one flight. The differences
can include fast motion smoothed out by the receiver fit, accelerometer
gain or bias, gravity assumptions, timing, or motion at the IMU that
differs from motion at the receiver antenna. The result gives a concrete
test for the next step: quantify how much unresolved motion changes
the raw magnitude in the middle window before treating force differences
as calibration or setting an aircraft prediction-error scale.

[Plan and reproduction](ESA_MATCHED_FORCE_PLAN.md) ·
[Frozen inputs](esa-matched-force-freeze.json) ·
[Detailed results](esa-matched-force-result.json)
