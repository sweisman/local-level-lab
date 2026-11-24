# Apply the recorded receiver clock correction to the Nuuk apron check

Keep the exact source excerpt, satellite screens, position assumptions
and finite allowance from the [first plan](ESA_APRON_CARRIER_PLAN.md).
That run stopped before estimating any range residuals because the
receiver epoch records contain nonzero clock offsets.

The observation header leaves the receiver-clock-applied flag at its
default of zero. Use the RINEX receiver clock correction. Subtract
the offset from the receive time and subtract its speed-of-light
equivalent from both code and phase in metres. The two corrections
preserve the derived satellite transmit time. The phase correction
is common across satellites at each epoch. Continue screening raw
continuous arcs before applying any corrections. Reject missing
offsets, offsets larger than 1 ms and adjacent changes over 2 μs.
[RINEX 3.04 receiver clock convention](https://files.igs.org/pub/data/format/rinex304.pdf)

Use the same one-thread, 260-check and 60-second allowance for this
separate corrected comparison. Preserve the stopped original run
and its one charged check.
