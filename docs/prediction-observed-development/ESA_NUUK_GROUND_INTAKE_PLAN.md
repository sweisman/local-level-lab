# Intake the permanent Nuuk receiver on the development flight date

Use the 30-second `NUUK00GRL` observation day published by SONEL for
6 July 2023 and the already sealed half-second AIR1 aircraft excerpt from
the same date. The sources and flight time are chosen by proximity and
overlap. Use one compressed ground file under 6 MB, one expansion with the
same verified GSI converter source as the Reykjavík intake, and the 17
integer 30-second targets within the frozen aircraft excerpt. This is a
data check with zero fits or reserved flight reads.
[SONEL data access](https://www.sonel.org/Data-access) ·
[Permanent station provenance](https://go-gnet.org/station-summary/nuuk) ·
[Aircraft carrier study](ESA_SHARED_MOTION_CARRIER_RESULT.md)

Require declared RINEX 3.05, GPS time, the permanent Nuuk marker, the
expected 30-second schedule and the original compressed and expanded
hashes. Preserve the ground header and selected records. Match exact
GPS seconds and signal identifiers. Require code and phase on both
`C1C`/`L1C` and `C2W`/`L2W`, and break a continuous arc at an event,
missing intermediate aircraft epoch or reported loss-of-lock flag.
Report the supported satellites and contiguous intervals, including
those inside the frozen two-minute shared-motion test. Interpret the
30-second station as a lower-rate comparison alongside the pending 1 Hz
Nuuk Museum receiver. This step verifies coverage and writes no position
or error estimate.
