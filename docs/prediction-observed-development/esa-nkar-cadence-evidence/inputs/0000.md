# Check the archived carrier signal at the Nuuk receiver's cadence

The [Nuuk Museum catalogue](ESA_GROUND_REFERENCE_AVAILABILITY.md) lists a
1 Hz file on the development flight date. Before ground observations are
available, check how much of the saved aircraft range signature remains
when it is reduced to that cadence. The only input is the 240 signed
half-second changes from the [completed carrier comparison](ESA_SHARED_MOTION_CARRIER_RESULT.md).

Sum each consecutive pair ending at the next integer GPS second, using only
satellites present in both saved changes and with archived final clocks.
Recenter the sum on those satellites to remove the common receiver-clock
term. Preserve the signed sums, paired times and satellite identities. Report
the required cancellation, archived correction and remaining difference in
range units and in range per second, together with their signed alignment.
No observed sample is interpolated. The calculation sums the published pair
models, so it does not establish that a new direct model of the one-second
endpoints would choose identical satellite ephemerides.

Allow one task with 120 two-row sums, a setup step and a 60-second
cooperative cap. Use one numerical thread and the same finite technical
recovery policy as the earlier carrier check. There are no new receiver or
aircraft fits and no reserved flight data are opened. This analysis cannot
verify actual ground coverage, differential-range accuracy or flight-level
prediction uncertainty.
