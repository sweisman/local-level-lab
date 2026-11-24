# Compare the two nearby Nuuk receivers on the same flight interval

Use the verified permanent Nuuk one-second excerpt and the sealed Nuuk
Museum range residuals from ESA development recording 187. Use only
GPS seconds 388614–388734 in week 2269. Hold the aircraft ranges, model
score gap, score weights, satellite orbit and clock products, and
atmospheric model fixed. Apply the established second-by-second GPS
carrier screen to the new station, with original L1C and L2W phases and
the recorded Doppler and lock indicators. Keep the original legacy
signal labels for the museum receiver.

For each second, keep satellites supported at both ground stations and at
both intervening aircraft half-second steps. Subtract each receiver's
mean across those same satellites to remove its clock change. Keep an
interval only when at least five satellites remain. Report the number of
intervals and satellites retained, station-to-station range difference,
and the signed projections onto the saved aircraft score direction.

If both stations see an identical shared range error, compute the smallest
possible worst-station local RMS error with no constraint on the score
and with a signed score change equal to the full gap in either direction.
For context, compare the Nuuk–Nuuk and Nuuk–Qaqortoq differences again on
the intersection of all three stations' valid satellites. These are
conditional comparisons. They leave the actual errors local to the
aircraft and differences in atmospheric propagation open.

One task uses one worker and one numerical thread. Allow one setup, 120
one-second range calculations and three conditional bounds. Allow 60
seconds of cooperative run time and preserve charges and failure evidence.
No Earth-model fits, original archive transfers or reserved flight reads.
