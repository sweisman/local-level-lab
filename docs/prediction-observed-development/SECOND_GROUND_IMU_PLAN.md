# Second raw iMAR ground baseline

Use the second interval selected solely by receiver speed in the
[second receiver control](SECOND_GROUND_INTERVAL_RESULT.md). Its time bounds
are fixed before reading the corresponding IMU rates. Verify the same
original `187_rqh01.txt` hash and use the existing strict iMAR parser and
unchanged raw-rate aggregator from the first ground control. Intersect with
the instrument's published timestamp coverage; require at least ten minutes
and reject gaps above 1.5 nominal sample periods. Keep every selected sample.

Save the second unadjusted X/Y/Z rate mean, vector magnitude, minute means,
half means, force and temperature context. Compare the two ground intervals'
mean magnitudes and vectors as descriptive instrument-output values. Do not
rotate either into geographic axes, assume the aircraft heading was the same,
subtract a predicted field, estimate a sensor bias, fit an Earth model or
open reserved ESA groups. Hash both selections, the original IMU, source
code and this plan. Use one thread and zero fit starts.

The two locations have nearly the same latitude but are about five hours
apart. A repeated norm could motivate a later field analysis; it would not
by itself distinguish a background field from bias, processing or platform
motion. A changed norm would also need those possibilities separated.
