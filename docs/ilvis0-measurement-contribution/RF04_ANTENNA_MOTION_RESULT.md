# Can antenna separation account for the RF04 discrepancy?

The antenna separation inferred from earlier observations reached the
**42 m airframe limit** in all six cases. The north error slightly
increased on the later two-second windows and decreased only modestly
on the longer windows. These fits supply no reliable correction for
the separation between the two antennas. [Frozen plan](RF04_ANTENNA_MOTION_PLAN.md)

| Window | Later north RMS, before → after, m/s² | Later north windows beyond rounding alone | Later north windows beyond rounding and sampled antenna motion |
| --- | ---: | ---: | ---: |
| 2 s | 0.00562 → 0.00564 | 12 of 118 | 2 of 118 |
| 6 s | 0.00296 → 0.00270 | 40 of 118 | 9 of 118 |
| 10 s | 0.00211 → 0.00196 | 49 of 118 | 11 of 118 |

The table uses the onboard position track. The carrier-phase track
left the same counts beyond the combined allowances. The three window
lengths overlap in time. The pointwise allowance permits a different
displacement to maximize the effect in each window. The RMS correction
uses one displacement per fit for all later
windows. The 42 m radius encloses the diagonal of the published aircraft
dimensions, about 41.7 m. The illustration using a 4.3 m longitudinal
offset gives a north effect below 0.00008 m/s² RMS for each width.
The 4.3 m in NCAR’s report refers to its own GPS antenna and inertial
unit. [Aircraft dimensions](https://archive.eol.ucar.edu/raf/Aircraft/gv/gvspecs.html) ·
[NCAR antenna discussion](https://ncar.github.io/aircraft_ProcessingAlgorithms/3-the-state-of-the-aircraft#global-positioning-systems)

The earlier data barely distinguish the weakest displacement direction.
Its singular value is about a quarter of one percent of the strongest.
Without the size limit, the fits would require 473 to 1,635 m of
displacement. The sampled-motion calculation and the rounding scenario
also leave several later north discrepancies above their combined
allowance. Faster attitude measurements or independently surveyed
antenna locations could test explanations beyond these one-second reports.
[Receiver reporting check](RF04_VELOCITY_RESOLUTION_RESULT.md)

All seven charged operations completed on one numerical thread. The same
saved receiver support and split replayed without new Earth-model fits,
original IMU decoding or reserved ESA reads.
SHA-256 `a73f186d7ad43333e2469484504dd7263923c427d246809c3d2e036ad5a96fa6`.
[Machine-readable result](rf04-antenna-motion-result.json) ·
[Frozen execution evidence](rf04-antenna-motion-evidence/README.md)
