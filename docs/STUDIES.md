# Study index

The main results are organized by the question each study answered. The [detailed study record](STUDY_RECORD.md) preserves the full sequence, including failed tests, numerical recovery, and links to the original reports.

## Airborne measurements

| Study | What it added |
| --- | --- |
| [Applanix archive decoding](ILVIS0.md) | Recovered recorded gyro and accelerometer increments and the primary GPS stream, with separate provenance for the combined navigation solution. |
| [Flight-stretch selection](ilvis0-highspeed-segments-20261008/ELIGIBILITY.md) | Selected 53 stretches totaling 424.3 minutes using measurement quality, duration, and ground speed. |
| [Original comparison and numerical recovery](CURRENT_STATUS.md) | Completed 12 initial comparisons and 41 later ones on the same selected stretches. All 53 favor the specified-field globe under both processing assumptions. |
| [Recording groups and matched field comparisons](analysis-provenance/NASA_ZERO_FIELD_BY_GROUP.md) | Grouped overlapping evidence and showed how the fitted geometry result changes when both models use zero background field. |
| [Raw gyro visualization](ilvis0-gyro-overview/README.md) | Displays the recorded pitch channel before adding GPS information or fitting corrections. |
| [Geographic gyro prediction](ilvis0-gyro-companion-v2/INTERPRETATION.md) | Compared measured pitch rates with fixed geographic predictions. The specified-field globe had the smallest median error in the descriptive check. |
| [Measurement contribution and controls](ilvis0-measurement-contribution/README.md) | Tested how gyro, acceleration, GPS coordinates, and height affect model comparison. The available force-only checks leave shape unresolved. |

## Prediction and independent validation

| Study | What it added |
| --- | --- |
| [NASA matched forecasts](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md) | Verified 15 of 16 retrospective forecasts. Globe gave lower 3D error at the same specified field in all four groups, and three specified-field globe forecasts met all position limits. |
| [NASA forecast extension](prediction-group-transfer/REMAINING_GROUPS_PREDICTION_RESULT.md) | Extended the retrospective check to 20 groups and retained all failed fits alongside the nine groups with usable later forecasts inside the development reference. |
| [ESA receiver and IMU method](esa-development-selection-v2/README.md) | Qualified the software path for the ESA recording format and selected development windows using receiver data and completed IMU support checks. |
| [ESA matched forecasts](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md) | Found a globe advantage on withheld positions in two complete settings on one development flight. Two other settings remain unresolved because the matched disc fits did not converge. |
| [Solver and memory checks](mixed-tangent-hybrid/ESA_DISPATCH_SCOPE_RESULT.md) | Verified agreement between two globe solvers on one development recording. [The structured receiver calculation](prediction-observed-development/STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md) avoids a dense matrix for long tracks. |
| [Receiver and ground-reference checks](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) | Checked the effect of different GPS reconstructions and compared airborne satellite measurements with two ground receivers. Shared aircraft errors remain open. |
| [Generated-data uncertainty validation](prediction-validation-continuation/README.md) | Completed all 4,344 fits and passed a fixed coverage test across 181 simulated cases. The result applies to the simulated conditions. |
| [Flight-group decision method](FLIGHT_GROUP_DECISION.md) | Tested how the proposed rule handles dependent groups, failed fits, and keeping the field comparison behind the shape decision. Aircraft calibration remains open. |
| [Reserved ESA groups](external-imu-data/ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md) | Found ten provisional windows across seven groups. [A second check](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md) verified one 20-minute IMU timestamp slice in each group. |
| [Evidence and reproducibility](PAPER_DATASET.md) | Links fitted and prediction results by recording group, with frozen source and report verification. |

The [planned GIRAFE clock check](prediction-observed-development/ESA_GIRAFE_LEVEL1_CLOCK_PLAN.md) awaits excerpts covering the earlier flight and score intervals.

[The current plan](NEXT_STEPS.md) explains what is left. The [stationary ground experiment](STATIONARY.md) is a separate consumer-IMU project in development.
