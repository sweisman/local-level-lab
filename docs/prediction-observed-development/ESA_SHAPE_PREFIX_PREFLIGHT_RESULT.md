# First check on the original ESA packets

The disc calculation matched both sealed reference positions from
recording 187. The globe calculation reached the 50-second cooperative
limit before reporting a bound. The two charged outcomes are preserved.
This run produced no matched comparison between the models.

| Saved fit | Query times | Maximum centre difference | Result |
| --- | --- | ---: | --- |
| Zero-field globe | 0.551 and 1.551 s | — | Bound stopped at its time limit |
| Zero-field disc | 0.551 and 1.551 s | 1.42 nm | Both centres matched |

Each model had 470 original packets available after accounting for the
local clock range. The disc calculation took 49.0 seconds and visited
those packets once for force integrals. It retained all 27 physical
and 24 shared derivative columns. The
[frozen plan](ESA_SHAPE_PREFIX_PREFLIGHT_PLAN.md) used two bound calls,
zero new native forecasts, and no fits or reserved data.

The disc’s unshared position remainder was at most 2.58 mm at the first
query and 7.94 mm at the second. Treating each shared coordinate as free
within its full normalized range raises a simple per-coordinate upper
estimate to about 0.625 m and 1.22 m, respectively. The largest
contributions at the second query come from the initial lever term and
reference acceleration. This loose estimate exceeds the sufficient
4.03 cm target. The shared terms describe the same calibration errors
across all reports, so the next bound must preserve that connection and
use the constraints from the earlier fit.
[Position-error target](SHAPE_REMAINDER_METRES_RESULT.md).

The original record contains 155,868 packets. The observed packet cost
makes a direct full-history run impractical at this speed. Faster packet
propagation and a useful bound on the jointly allowed calibration errors
remain open.

A local profile on 48 generated 5 ms packets used 41 propagation steps.
In that diagnostic, building and checking the source intervals took
about 3.6 seconds in total. The two velocity updates per step took about
2.0 seconds. These costs are inside the packet loop, after the force-integral
scan was shared across queries. This identifies where to work before a
longer preflight.

[The faster matched check](ESA_SOURCE_TRANSFER_CHECK.md) subsequently completed
both models under the same time limits. The original timeout stays sealed.

[Sealed preflight evidence](esa-shape-prefix-preflight-evidence/README.md).
