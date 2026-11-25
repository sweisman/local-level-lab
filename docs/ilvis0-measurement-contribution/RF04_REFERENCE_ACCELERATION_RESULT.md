# RF04 receiver acceleration cross-check

Over the later 118 windows, horizontal acceleration estimates from the
saved GPS positions and the RF04 reference receiver velocities differed
by **0.075 m/s² RMS over two seconds** and **0.020 m/s² RMS over ten
seconds**. Almost all of the disagreement was in the east component.
The carrier-phase position path and shifts of ±0.4 seconds gave
essentially the same result. [Frozen plan](RF04_REFERENCE_ACCELERATION_PLAN.md)

| Window | Earlier horizontal RMS | Later north RMS | Later east RMS | Later horizontal RMS | Later horizontal 95th percentile |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2 s | 0.0477 | 0.0056 | 0.0744 | 0.0746 | 0.1833 |
| 6 s | 0.0226 | 0.0030 | 0.0368 | 0.0370 | 0.0604 |
| 10 s | 0.0140 | 0.0021 | 0.0201 | 0.0202 | 0.0327 |

All values are in m/s². The table uses the onboard position path at
zero shift. Every setting used the same 265 earlier and 118 later centers
and the matching whole-second endpoints for each width. The acceleration
in this test is the change in the reported north and east velocity
components divided by elapsed time. It uses neither the inertial
navigation solution nor a geometry or background-field fit.

At one gravity, a 0.12° change in force direction corresponds to about
0.02 m/s² transverse to that force. Even at ten seconds, 55 of the 118
later windows exceeded that descriptive scale in the unshifted onboard
case. These are overlapping windows, and the cross-check uses longer
averages than the earlier force-direction comparison. It measures
disagreement between the two ways of estimating acceleration. Which
source is responsible, how much changing antenna position contributes,
and what happens within a second remain open. [Force comparison](RF04_FORCE_AVERAGE_RESULT.md)

The sealed run completed all 19 charged operations and produced 18
comparisons on one numerical thread. It started zero Earth-model fits,
decoded no original IMU packets and read no reserved ESA data.
SHA-256 `073a07459f2322fec3cde01963c5efee1a4d6531d4c34087484e08a7471cd052`.
[Machine-readable result](rf04-reference-acceleration-result.json) ·
[Frozen execution evidence](rf04-reference-acceleration-evidence/README.md)
