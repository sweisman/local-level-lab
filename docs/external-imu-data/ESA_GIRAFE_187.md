# A separate motion sensor on the ESA development flight

The campaign lists raw acceleration and angular-rate data from the
stabilized GIRAFE platform, plus raw acceleration observations from
the cold-atom instrument. The platform moves relative to the aircraft.
Its angular rates would need a measured relationship to the airframe
before they could check aircraft turning. The campaign's fused navigation
attitude uses the iMAR being tested, so it cannot supply that check.
[Campaign data products and methods](https://essd.copernicus.org/articles/17/1667/2025/#section3)

An authenticated directory listing for the opened development flight
`/lvl0/187/girafe/` reports the following files. Exact time coverage
and data format still need checking.

| File | Bytes |
| --- | ---: |
| `GIRAFE_raw_acc_187a-Nuuk-Rey.txt` | 16,883,030 |
| `GIRAFE_raw_acc_187b-Rey-Aku.txt` | 6,277,733 |
| `LOGXIO_06_07_2023 _01.Asc` | 1,860,304,779 |
| `LOGXIO_06_07_2023 _02.Asc` | 534,526,924 |

The first 16,384 bytes of the first platform log contain 212 complete
rows of seven numeric columns and no header. Every complete row is 77
bytes including its line ending. The first column runs from 696.8154 to
697.0215. Its increments of 0.0009 or 0.0010 are consistent with a uniform
1/1024-second interval printed to four decimal places. This fits the
prefix. The full-file layout, time origin and column units remain open.
The range is retained locally as
`data/external-imu-survey-20261018/esa-sample/girafe-187-platform-01-prefix.asc`
with SHA-256 `222235a6de00797770460d01b2aa4e04a4e73f38900268f1d830ad3129db536e`.
The [interior byte probes](../prediction-observed-development/ESA_GIRAFE_PLATFORM_PROBE_RESULT.md)
find variable-width rows with the same printed 1,024 Hz clock phase at
widely separated locations. Absolute time alignment and channel units
remain unverified.
The [vertical timing check](../prediction-observed-development/ESA_GIRAFE_PLATFORM_VERTICAL_HOLDOUT_RESULT.md)
finds the same candidate clock offset in three new excerpts. One of the
three meets the correlation requirement. Fine timing and force response
still need separate checks.
The two smaller acceleration files are now verified locally. Their
header gives UTC seconds from flight-day midnight, one acceleration
channel from the atom instrument and two horizontal channels from
quartz sensors. The Nuuk–Reykjavík file contains 234,193 samples and
overlaps all eight frozen iMAR windows at 10 Hz. Each window contains
3,990 GIRAFE rows. The Reykjavík–Akureyri file contains 87,132 samples
and overlaps none of those windows. [Coverage and original-file hashes](esa-girafe-187-acceleration-inventory.json)

The files establish time overlap on the declared clocks. The filter
delay, platform motion and accuracy of the separate force measurement
still need checking. The [matched force comparison](../prediction-observed-development/ESA_GIRAFE_FORCE_OVERLAP_RESULT.md)
finds close agreement in force changes and a persistent difference in
average magnitude. Heading remains outside that check.

The platform log is a possible second source for direction changes.
Once its clock and channels are qualified, each instrument can use its
own angular rates to put its force measurements into one frame. Angles
between pairs of averaged force vectors then cancel any fixed starting
orientation between the instruments. Movement of the platform and the
physical separation of the sensors can still change the measured forces.
These effects need their own check before interpreting a disagreement.

The [local rate screen](../prediction-observed-development/ESA_GIRAFE_PLATFORM_RATE_RESULT.md)
gives a candidate interpretation of the last three columns in their original
order as radians per second. It helps at tenth-second separation and gives
larger errors at one second. The mapping and fine absolute timing remain
unqualified for a comparison of angular changes with iMAR.

The [ground comparison](../prediction-observed-development/ESA_GIRAFE_GROUND_RATE_RESULT.md)
finds a consistent strong force match when iMAR is queried 0.1 seconds
earlier than the proposed time. The fixed-time gate fails, and the same
rate convention worsens both direction comparisons. Fine alignment and
the channel interpretation still need separate validation.

The [finer lag grid](../prediction-observed-development/ESA_GIRAFE_FINE_LAG_RESULT.md)
preserves the 100 ms ground shift. The first and last airborne clips favor
different shifts, and the middle clip remains weak at every tested lag.

## Processed records with GPS timestamps

The ESA archive also has processed acceleration exports for GIRAFE and iMAR
on the Nuuk–Reykjavík flight. Both prefixes contain GPS week and seconds,
receiver position and velocity, and bank, elevation and heading. The GIRAFE
file gives vertical acceleration at 10 Hz and a two-second filtered channel.
The iMAR file gives all three axes at about 300 Hz. These columns make it
possible to check how the campaign timestamps its processed outputs against
the original records. The headers leave the source of the GIRAFE attitude
columns and the sensor-to-export delay unspecified.
[Campaign data and processing description](https://essd.copernicus.org/articles/17/1667/2025/)

The first 8,192 bytes of each export are retained under
`data/external-imu-survey-20261018/esa-sample/`. Both came from
`/lvl1/accelerations/` on the ESA distribution server.

| Prefix | SHA-256 |
| --- | --- |
| `187a_girafe_accelerations-prefix.txt` | `0b26c5ad28effe883eeb3d8dc9e200bfee939f735f185393dd1033ab99e9cc9d` |
| `187a_imar_accelerations-prefix.txt` | `1bca89a7e841a86f35be7d89ccec1bf09b61bfd2f2178208e8f861d56ebde5ab` |

Two range requests for later intervals both returned data from the start
of the GIRAFE export. The planned timing comparison awaits excerpts with
verified coverage of the intended intervals.
[Clock comparison plan and acquisition check](../prediction-observed-development/ESA_GIRAFE_LEVEL1_CLOCK_PLAN.md)
