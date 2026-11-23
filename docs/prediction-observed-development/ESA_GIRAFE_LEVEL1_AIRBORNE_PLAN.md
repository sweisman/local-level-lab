# Test whether the GIRAFE vertical export match carries over to flight

Use the exact intervals in the [acquisition plan](ESA_GIRAFE_LEVEL1_AIRBORNE_ACQUISITION.md).
Check all 100 samples in the 10-second interval and all 1,200 in the
two-minute score interval. Freeze the reversed export sign and zero lag
from the [recording-start check](ESA_GIRAFE_LEVEL1_PREFIX_RESULT.md).
For both intervals report all 41 time shifts and the same one-to-one
matches and RMS threshold. The fixed zero-lag match must be the unique
match within 0.000001 m/s² RMS in each interval.

Freeze the transfer receipt, processed response, verified shorter prefix,
original acceleration file and recording-start results. Use the same
clock conversion and shift limits, one task and one local thread. Charge
one scan of the bounded prefix and at most 240,000 original rows, then
82 comparisons. Allow 30 seconds and zero model fits or native calls.
The test is limited to the vertical export on development recording 187a.
