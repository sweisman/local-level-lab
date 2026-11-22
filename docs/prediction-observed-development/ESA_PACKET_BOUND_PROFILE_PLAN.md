# Profile the recorded packet-bound calculation

The [short recorded preflight](ESA_SOURCE_TRANSFER_CHECK.md) verified both
outward reports for each candidate, but processing the full 155,868-packet
history remains too slow. Profile the actual calculation before choosing
which part to accelerate.

Reuse the sealed 470-packet prefixes, two query times per candidate, original
physical boxes and original numerical environment. Restore the complete
checked source package from the recorded preflight in a separate interpreter.
Allow profiling time without changing the work limit or arithmetic. Require
byte-identical bound reports and the original packet-work counts before
interpreting a completed profile as representative of that calculation.

Record process CPU, elapsed time, calls, self time and cumulative time.
Profile the packet-bound calculation after compilation. Report both self time
and cumulative time because cumulative values include nested functions and
cannot be added across them. Keep any incomplete runs and their profiles.

Use two tasks on one numerical thread while the independent solver benchmark
continues. Allow one bound charge and up to 1,280 steps per task, with a
180-second cooperative allowance for each profiled calculation and a
400-second overall allowance. Use the qualified technical recovery rules.
No model fit, new trajectory integration, receiver position read or
confirmation-flight access is part of this profile.
