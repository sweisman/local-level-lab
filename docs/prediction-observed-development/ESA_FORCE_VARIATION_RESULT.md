# Fast changes in direction explain the large force-magnitude mismatch

In the middle ESA training window, the receiver and accelerometer agreed
much more closely after the accelerometer vectors were averaged over
0.1 seconds before taking their magnitudes. After applying an offset
estimated on the other two windows, disagreement fell from **0.065 to
0.00090 m/s² RMS**. A 1-second vector average gave nearly the same result.

| Training window | Magnitudes first, RMS | 0.1-second vectors first, RMS | 1-second vectors first, RMS |
| --- | ---: | ---: | ---: |
| 187-042470-044870 | 0.00697 | 0.00389 | 0.00388 |
| 187-049554-051954 | 0.06487 | 0.00090 | 0.00091 |
| 187-058525-060925 | 0.00487 | 0.00263 | 0.00250 |

All values are in m/s². Each entry uses the same 32 receiver supports
and an offset estimated on the 64 supports from the other two windows
under that averaging method.

Taking a magnitude counts sideways motion in either direction as an
increase. Averaging the vectors first allows opposing components to
cancel. At the largest discrepancy, a 0.1-second vector average removed
0.16511 m/s² from the original 0.17558 m/s² excess before applying any
offset. At that point the logged rotation could account for at most
0.000016 m/s² of the change if the underlying force direction were fixed
and the logged angles described the full relative rotation. The rapid
variation in the observed force vectors goes well beyond that rotation
check. The comparison cannot apportion it between aircraft motion,
vibration and instrument effects.

The replay reproduced the original magnitude and sample count at all
96 centers. It made 192 comparisons using 719,097 inertial samples and
ran no trajectory fits. The vector averages are a diagnostic of the
scalar force test. Their success does not justify replacing the raw
increments in the navigation fits or transferring an error scale to
other flights. Two of the three windows still exceed the working
0.001 m/s² drift scale after the same correction.

The next check can use the amount of fast force variation as a measured
input and test whether it tracks errors in already scored aircraft
forecasts. The improvement in force magnitudes does not establish an
improvement in predicted positions.

[Plan and reproduction](ESA_FORCE_VARIATION_PLAN.md) ·
[Frozen inputs](esa-force-variation-freeze.json) ·
[Detailed results](esa-force-variation-result.json)
