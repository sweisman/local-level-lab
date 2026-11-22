# Check the candidate platform clock against a separate instrument

The [vertical response diagnostic](ESA_GIRAFE_PLATFORM_VERTICAL_RESPONSE_RESULT.md)
found correlations above 0.93 at 1.1-second averaging when comparing the
GIRAFE platform raw values with the timed GIRAFE vertical record. Use
the same fixed candidate offset, 38,474.26739992 seconds, for a comparison
with the separately recorded iMAR acceleration. The iMAR data did not
select this offset. The two instruments remain on one aircraft.

Use the three [saved platform excerpts](ESA_GIRAFE_PLATFORM_VERTICAL_HOLDOUT_RESULT.md)
after their original overlap and two-second guard. Read the matching
iMAR intervals, plus two seconds on either side, from the verified
original recording 187. Use force magnitudes from the three iMAR
accelerometer channels and from the first three candidate platform
channels. Magnitudes allow comparison while the axes are unresolved.
Record the platform's candidate vertical magnitude as a separate diagnostic.
Sensor spacing and platform movement can change the signals.

Use time-weighted tenth-second cells on the candidate common clock and
the same 1.1-second moving average and first differences as the previous
response check. Compare all complete supports. Report each correlation
at the candidate time and the best nearby correlation within two seconds
at tenth-second steps. Require at least 0.70 at the candidate offset
with the best nearby time within 0.2 seconds for every excerpt. Seal any
missing or failed comparisons. No fit over sensor orientation, scale,
clock drift or averaging width. Keep the earlier qualifications intact.

Use one local worker and one numerical thread with a 60-second limit.
Permit one complete original-file hash pass, three bounded iMAR slices
of up to 5,000 sample intervals, and the three verified saved platform
ranges. Charge a fixed 41 local shift comparisons per signal per range.
The scope is opened recording 187. No network calls, reserved flight
groups or Earth-model fits.
