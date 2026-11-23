# The original and processed GIRAFE vertical samples match at the start

All **1,320 samples** in the saved processed excerpt match the original
vertical acceleration exactly after reversing the processed sign. Their
GPS time tags coincide. Zero shift was the only one of 41 tested shifts
to meet the fixed agreement threshold in both blocks.

| Consecutive block | Samples | RMS at zero shift, recorded signs | RMS at zero shift, reversed export sign | Smallest RMS at a different shift, reversed sign |
| --- | ---: | ---: | ---: | ---: |
| First | 660 | 19.64349 m/s² | 0 m/s² | 0.02403 m/s² |
| Second | 660 | 19.64348 m/s² | 0 m/s² | 0.03219 m/s² |

The range requests returned the beginning of the file. This check covers
132 seconds there, starting at GPS second 384898.51739992 in week 2269.
It identifies the relative timestamp and sign for the copied vertical
values. Physical sensor latency, horizontal quartz timing and matches
during the later airborne intervals remain open. [Airborne acquisition plan](ESA_GIRAFE_LEVEL1_AIRBORNE_ACQUISITION.md)

The first local worker stopped before scoring because the accounting API
rejected a batch charge. Its terminal receipt preserves the charged scan.
The [recorded-sign comparison](ESA_GIRAFE_LEVEL1_PREFIX_PLAN.md) and the
[reversed-sign follow-up](ESA_GIRAFE_LEVEL1_PREFIX_SIGN_PLAN.md) then
completed 82 checks each. The sign follow-up used the same data and was
motivated by the first comparison. Eight software tests passed. The
study used no fitted Earth models or reserved recordings.
[Scores, hashes and accounting](esa-girafe-level1-prefix-result.json)
