# Check the calibration-width cache on complete packet prefixes

The [runtime profile](ESA_PACKET_BOUND_PROFILE_RESULT.md) showed thousands of
exact affine-radius calls on the same calibration box. Use the existing
bounded cache for those exact box widths. Keep the rational fallback and
every outward rounding operation.

Run the archived and revised code on the two sealed recorded prefixes.
Restore all archived dependencies in separate processes and replace exactly
one Python source file in the revised run. Reverse the order for the second
candidate. Check both bound files against their original hashes and compare
packet-work counts. Measure process CPU and elapsed time without function
profiling. Require a speed ratio of at least 1 for each bound and a median
ratio greater than 1.05 before claiming that this change speeds up the
recorded prefixes. This is a checkpoint for longer calculations.

Use two tasks and two one-thread workers. Give each task two bound charges
and 2,560 steps, with 180 seconds per variant and 420 seconds overall. Retain
any nonmatching or incomplete result. Use the qualified recovery rules.
No new fit, new observation or reserved flight is used.
