# The wide ESA bound comes from letting shared calibration terms move independently

The saved calibration design can erase the **25.41-unit** globe–disc
forecast difference when its shared terms are allowed to vary independently.
Feasible examples moved the globe forecast **52.00 units** and the disc
forecast **50.34 units** toward each other while improving both earlier
GPS scores. This accounts for almost all of the previous **102.62-unit**
upper bound.

Applying one calibration to all the shared terms changed the result. With
the same proposed physical movements, every linked example failed the
earlier GPS check, even at one eighth of the displacement. A separate
search using only the physical columns produced linked examples that
passed. The largest scored movement among those examples was **0.190**
units for globe and **0.199** for disc.

| Check on the saved design | Globe | Disc |
| --- | ---: | ---: |
| Movement with independent shared terms | 52.005 | 50.344 |
| Earlier loss increase for that example | −4.114 | −3.934 |
| Smallest earlier loss increase after linking the same proposal | 74,070.648 | 70,292.956 |
| Largest feasible movement from the physical-column proposal after linking | 0.190 | 0.199 |

The earlier loss increase limit was 0.01. The linked examples are
individual points, so they establish no upper bound across all physical
calibrations. The next check should constrain all 24 shared terms in
the earlier-fit region, using the same physical calibration throughout.
The full nonlinear propagation error and aircraft prediction uncertainty
remain open.

Both candidates completed all 12 checks each in the
[corrected freeze](ESA_CALIBRATION_WITNESS_PLAN.md). The first freeze
stopped at the accounting check before either numerical proposal.
The corrected run started no new trajectory fits and used no later GPS
positions. It preserved all passing and failing points.

[Sealed inputs, source and results](esa-calibration-witness-evidence/README.md).
