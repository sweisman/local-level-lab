# Raw pitch rates compared at the same background field

**When both shapes use the specified background field, the globe prediction
is closer to the recorded pitch rates across the tested assumptions.**
The recording-group median favors the globe even when each group can use
its own setting for bank, pitch, heading relative to course and upstream
field removal. When both shapes use zero field, the median can favor
either shape.

The table gives the median difference in absolute pitch-rate error, in
degrees per hour. Positive values favor the first model in each row.
Every group has equal weight, including groups with multiple stretches.

| Comparison | Level reference | Same assumptions for every group | Assumptions may differ by group |
| --- | ---: | ---: | ---: |
| Globe vs. disc, specified field for both | +6.82 | +3.72 to +7.06 | +1.10 to +9.06 |
| Globe vs. disc, zero field for both | +4.62 | −1.51 to +4.82 | −3.63 to +6.05 |
| Specified field vs. zero field on a globe | +2.00 | +0.62 to +3.87 | +0.10 to +4.40 |

For the level reference, 26 of 27 groups have lower error on the globe
at the matched specified field. Eighteen groups favor that prediction in
all 81 settings. The field comparison on a globe has a much smaller
worst-case median margin of 0.095°/h. The individual group results are in
the saved ledger. The 27 groups account for known overlap and can still
share instrument and survey effects.

The comparison uses the preserved raw gyro rates. Receiver positions
supply the track for the geographic predictions. A saved field subtraction
lets the replay add the same specified field to the disc in its own
predicted aircraft axes. Actual changes in aircraft attitude and sensor
mounting error remain unmeasured. The ranges apply to the fixed assumptions
tested here and the field magnitude is fixed in advance. These results
describe a comparison of pitch predictions. They do not establish an
independent shape decision, a freely measured field, or its cause.

The replay checked all 12,879 published rows for the 53 stretches against
their receipt and ran zero new fits. Two known-answer tests passed.
[Original gyro comparison](INTERPRETATION.md) · [Fixed analysis and commands](MATCHED_GROUP_PLAN.md) ·
[Source bindings](matched-group-freeze.json) · [Group results](matched-group-result.json).
