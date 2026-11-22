# The recorded position bounds grow too wide by 4.55 seconds

Both candidates completed all four recorded checkpoints. Every predicted
centre matched its archived forecast to within 1.5 nanometres. The bound
on nonlinear error exceeded the 4.03 cm engineering target at the third
checkpoint and continued to grow.

| Time from start | Zero-field globe, largest coordinate bound | Zero-field disc, largest coordinate bound |
| ---: | ---: | ---: |
| 0.55 s | 2.29 mm | 2.58 mm |
| 1.55 s | 7.24 mm | 7.93 mm |
| 4.55 s | 59.13 mm | 60.03 mm |
| 9.55 s | 447.97 mm | 457.10 mm |

At 9.55 seconds, the propagated position term contributes about 409 mm of
the globe's largest bound and 410 mm of the disc's. The receiver lever-arm
term adds about 39 mm and 47 mm, respectively. This locates the larger
source of growth in the propagation of the position bound. These values
are allowances across a calibration box, not measured forecast errors.

The 4.03 cm target assumes the separate earlier-loss remainder requirement
and the tested covariances. These short prefixes cannot settle the full
shape comparison. The current propagation method needs a tighter bound
or a justified smaller calibration region before a full-history proof can
use that target.

The two tasks completed in 180.2 seconds, with two bound charges and 12
local checks passed. They preserve all 27 physical and 24 auxiliary columns
and use no new fits, measured positions or reserved flights.

- [Frozen plan](ESA_PACKET_BOUND_GROWTH_PLAN.md)
- [Results and checkpoint summaries](esa-packet-bound-growth-result.json)
- [Verified evidence and complete bounds](esa-packet-bound-growth-evidence/README.md)
