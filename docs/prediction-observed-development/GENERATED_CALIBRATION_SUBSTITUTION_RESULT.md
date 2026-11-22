# Changing calibration alone makes these generated paths worse

The [frozen two-case control](GENERATED_CALIBRATION_SUBSTITUTION_PLAN.md)
reconstructed the exact generated IMU inputs and reproduced both sealed
baseline paths before scoring. It then replaced selected fitted values with
the values used to generate the data. **Everything else stayed at its fitted
value; nothing was refitted.** Both tasks passed their technical checks and
all eight native forecasts were charged and saved.

| Generated error law | Values replaced | Later horizontal error | Later vertical error |
|---|---|---:|---:|
| Increment | None: original fit | 109 m | 7.5 m |
| Increment | Sensor bias and gain | 995 m | 24.4 km |
| Increment | Gravity adjustment and clock | 684 m | 30.8 km |
| Increment | All fourteen | 517 m | 6.45 km |
| Point | None: original fit | 91 m | 3.2 m |
| Point | Sensor bias and gain | 1,354 m | 2.00 km |
| Point | Gravity adjustment and clock | 203 m | 4.47 km |
| Point | All fourteen | 1,241 m | 6.47 km |

The fitted calibration coordinates are strongly coupled to the other fitted
coordinates in these two examples. Replacing one block with its known truth
while holding the fitted initial state and other corrections fixed breaks
that compensation. The large changes show why a simple one-parameter
explanation of the original 91–109 m path miss would be unreliable. They do
**not** show that the true calibration is physically wrong or that the
recorded aircraft sensor behaves this way. A matched refit with a justified
constraint would answer a different question.

No aircraft recording was opened, no new fit was performed, and neither
generated path meets the [coded accuracy screen](GENERATED_ACCURACY_RULE_ERRATUM.md).
The aircraft error law remains unqualified; scientific decision: **abstain**.

[Verified machine report](generated-calibration-substitution-result.json) ·
[Known-calibration audit](GENERATED_CALIBRATION_RECOVERY_RESULT.md)
