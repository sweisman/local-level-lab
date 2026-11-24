# Match the aircraft and Nuuk Museum on the apron interval

Use the fixed [receiver-selected apron excerpt](ESA_APRON_CARRIER_RESULT.md)
and the original Nuuk Museum station day from the
[ground reference study](ESA_NKAR_GROUND_SCORE_RESULT.md). Verify the
original, compact and expanded RINEX hashes. Decode with the published
GSI Linux converter and record its executable hash. Retain only the
19 ground epochs from GPS second 383697 through 383715 in the study.

Reproduce the aircraft carrier residuals at the same assumed parking
position and with the same receiver-clock correction. For each integer
second, sum the two consecutive half-second residuals on their common
satellites. Compute the ground residuals with the same satellite
products and its saved antenna position. Retain at least five shared
satellites per pair and remove the common receiver clock from each
receiver on exactly that shared set.

Report the one-second aircraft RMS, station RMS, signed difference RMS
and correlation on the matched observations. A small difference may
support a common component. The two receivers can also have different
antenna effects, reflections and tracking. The residuals on the ground
give no upper bound on those effects during flight.

Use one numerical thread and at most 56 charged checks in a 60-second
worker. Limit intake to one archived station day, at most 40,000 epochs
up to this interval and the existing decoder size caps. Use no new
flight downloads, model fits or reserved aircraft observations.
