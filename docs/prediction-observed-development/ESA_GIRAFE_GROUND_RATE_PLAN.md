# Test the candidate platform rate convention during a low-speed stop

Use recording 187 and the first [receiver-selected ground stop](GROUND_IMU_RATE_RESULT.md)
in Greenland. Freeze the existing platform convention in radians per second,
in the original axis order and signs. Keep the tentative clock offset fixed
at 38,474.26739992 seconds from the platform clock to UTC seconds from
midnight. The [airborne rate screen](ESA_GIRAFE_PLATFORM_RATE_RESULT.md)
and [iMAR timing check](ESA_GIRAFE_PLATFORM_IMAR_FORCE_RESULT.md) remain
separate results.

## Acquisition

Choose the quarter, midpoint and three-quarter times of the saved IMU overlap
from the receiver-selected stop, rounded to whole GPS seconds. Estimate each
file offset using the saved first platform time, 696.8154 seconds, and the
prefix width of 77 bytes at 1,024 records per second. These estimates only
locate the raw ranges. Keep all three even if their sensor comparisons fail.

| Target GPS second | Target platform second | Estimated byte offset |
| ---: | ---: | ---: |
| 385574 | 1481.7326 | 61889151 |
| 386250 | 2157.7326 | 115190399 |
| 386927 | 2834.7326 | 168570495 |

For each offset, read 1 MiB and independently read 1,024 bytes starting
512 bytes earlier. Check that the last 512 bytes of the short read match
the first 512 bytes of the long read. Accept only complete reads, each with
an exact byte count and a recorded SHA-256. Require compatible recorded clock
phase and the first complete row within 30 seconds of the target. Retain the
earlier two-second guard after the overlap. Use the [bounded FTPS procedure](ESA_GIRAFE_PLATFORM_TRANSFER.md)
with one size check and one pair of reads per target. Defer the analysis if
the complete required inputs are unavailable.

## Local comparison

1. Use the declared platform rates to predict later force directions over
   tenth-second and one-second pairs. Score with the same averages and error
   measures used in the airborne screen. Keep the convention fixed.
2. Independently compare the platform force magnitude with iMAR in matching
   tenth-second cells. Read only the exact iMAR support under the candidate
   clock and two-second search guard. Apply the previous 1.1-second averaging
   and first-difference check. A time match needs correlation at least 0.70 at
   the proposed time and its best peak within 0.2 seconds.
3. Report all six direction errors and all three force matches. Interpret an
   excerpt as shared ground motion only if the separate iMAR match passes.
   The ground rate convention is supported across this check only if all
   three clips match iMAR and the gyro improves both separations in every
   clip. Even then, exact axis calibration and yaw remain open.

Freeze one local task with one worker and one thread, a 120-second limit,
one original iMAR hash pass, three verified range pairs, up to 14,000 platform
rows and 5,000 iMAR intervals per target, three direction comparisons at
both separations and 41 force-magnitude shifts per target. Report technical
or scientific failures as such. The worker has no network calls or Earth
model fits and cannot open reserved flight groups.
