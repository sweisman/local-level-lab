# Compare the one-second ground record with the aircraft score

Use only the previously frozen two-minute window of ESA development flight 187.
Read the original compressed Nuuk Museum station day and record the original,
expanded and decoder hashes. Retain the exact station epochs from that window,
the receiver clock declaration, original RINEX 2 signal labels, marker
coordinates and antenna offset. Ground times with unapplied recorded clock
offsets require a separate timing check before this comparison.

Keep only one-second intervals with normal station observations, unchanged
labels and compatible carrier flags at both endpoints. Require at least five
satellites also present in both aircraft half-second pairs. Use the two GPS
phase bands to remove the leading ionosphere term. Evaluate signed range changes
using the archived final satellite orbits and clocks, approximate station
antenna position and the existing atmosphere model. Subtract the modeled change
and remove the common receiver clock independently for both receivers. Leave
gaps as gaps. Legacy `L1` and `L2` labels still leave the exact tracking codes
and antenna phase-center behavior open.

Project the archived score weights onto the actually matched carrier totals.
Report the visible weight fraction, the signed aircraft and ground score
equivalents, and their difference. The comparison measures agreement on one
development recording. It leaves aircraft-specific errors, model errors shared
by both receivers, and the missing directions open. A small difference does
not itself certify a physical error bound or permit confirmation flights.

One task, one thread and a 180-second cooperative cap. Charge one setup and 120
interval checks, including unavailable intervals. The input decoder does no
scientific fitting. The study refits no models, reads no reserved flights, and
uses the same checked technical recovery as the earlier carrier comparisons.
