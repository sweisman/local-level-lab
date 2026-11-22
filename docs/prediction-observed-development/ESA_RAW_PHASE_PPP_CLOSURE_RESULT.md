# GPS position differences explain only part of the raw carrier differences

The position solutions from three receivers on the same ESA flight
capture some of the carrier differences. In the later two minutes,
projecting the position differences back onto the satellite directions
produces more error than predicting zero difference. This holds for
all three receiver pairs.

| Receiver pair | Earlier carrier RMS, zero → projected PPP | Later carrier RMS, zero → projected PPP |
| --- | ---: | ---: |
| `air1` and `mosaic03` | 5.15 → 4.80 mm | 5.26 → 5.65 mm |
| `air1` and `pwrpak7` | 5.51 → 5.05 mm | 5.60 → 5.71 mm |
| `mosaic03` and `pwrpak7` | 1.99 → 2.06 mm | 1.77 → 2.01 mm |

The direction of the differences still contains information. In the
later interval, the eastward changes inferred from the raw measurements
correlate **0.83 and 0.84** with the projected position changes for the
two pairs containing `air1`. Their northward and vertical correlations
are 0.40–0.52. The one-second carrier differences and the exported
position differences cannot be treated as the same error.

All 398 earlier intervals and all 120 later intervals match all three
GPS solutions. The original one-second clock break remains excluded.
Both tasks finished in 6.9 seconds with 519 charged calls, five software
checks passed, and no aircraft forecast was refitted. The receivers
share an antenna. The comparison leaves common GPS errors and absolute
position accuracy open.

[Frozen plan](ESA_RAW_PHASE_PPP_CLOSURE_PLAN.md) ·
[Verified evidence](esa-raw-phase-ppp-closure-evidence/README.md)
