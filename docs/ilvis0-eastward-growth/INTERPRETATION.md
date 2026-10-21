# The large allowance accumulates through velocity and position

**Six of eight traces pass exact predecessor checks.** The two fixed-zero
future queries reach the unchanged time limit. Their failures remain, and the
completed study will not be retried.

In the completed training queries, coordinate departure accounts for about
81% of the final eastward allowance. In the two completed future queries it
accounts for about 85%. Departure is accumulated from the residual velocity;
it is not an independent error in the coordinate formula or an error measured
on an aircraft.

The recorded force remainder is driven largely by the changing body-rotation
source. Its eastward allowance is around 0.007–0.008 m/s² at the completed
query endpoints, feeding a residual-velocity allowance around 0.055–0.068 m/s.
Clock-boundary intervals add visible growth near the final query. These are
nested conservative bounds, not measurements of sensor bias or drift.

The next method will target the source's Taylor remainder directly, using
rotation-product bounds and the same physical calibration and timing domain.
It must account for calibration denominators, clipping at packet boundaries,
arbitrary supplied derivative rows and numerical reference error. Mathematical
controls come before native installation or another complete prediction test.

No bound has been reduced and no aircraft fit has run. The 53-stretch findings,
failed regions and complete prediction-width target remain unchanged.

[Verified traces](README.md) · [Next method](NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
