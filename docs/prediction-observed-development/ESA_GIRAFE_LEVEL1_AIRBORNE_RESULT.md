# The GIRAFE vertical timestamps and sign match in flight

The original and processed GIRAFE vertical acceleration values match
exactly at the same GPS timestamps across both fixed airborne intervals.
The processed column uses the opposite vertical sign. That sign and zero
time shift were set using the [recording-start check](ESA_GIRAFE_LEVEL1_PREFIX_RESULT.md)
before comparing the airborne values.

| GPS seconds of week | Samples | RMS at zero shift with reversed export sign | Best RMS at any other shift |
| --- | ---: | ---: | ---: |
| 388215–388225 | 100 | 0 m/s² | 0.02020 m/s² |
| 388614–388734 | 1,200 | 0 m/s² | 0.06416 m/s² |

All 82 comparisons completed. Zero shift alone met the fixed threshold
in both intervals. Nine software tests passed. There were zero model fits
and zero reserved-flight reads.

The processed `z-acc` column adds no independent vertical measurements
on these intervals. The identical time labels establish how to match the
two files. The delay from physical motion to the shared samples and the
accuracy of the separate horizontal force channels remain open.

[Frozen comparison](ESA_GIRAFE_LEVEL1_AIRBORNE_PLAN.md) ·
[Acquisition receipt](esa-girafe-level1-airborne-acquisition.json) ·
[All scores and accounting](esa-girafe-level1-airborne-result.json)
