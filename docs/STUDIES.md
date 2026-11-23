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
| [Pitch rates at matched fields](ilvis0-gyro-companion-v2/MATCHED_GROUP_RESULT.md) | Gave each recording group equal weight. The pitch-rate comparison favored globe across the tested assumptions at the same specified field, while the zero-field ranking could change. |
| [Measurement contribution and controls](ilvis0-measurement-contribution/README.md) | Tested how gyro, acceleration, GPS coordinates, and height affect model comparison. The available force-only checks leave shape unresolved. |

## Prediction and independent validation

| Study | What it added |
| --- | --- |
| [NASA matched forecasts](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md) | Verified 15 of 16 retrospective forecasts. Globe gave lower 3D error at the same specified field in all four groups, and three specified-field globe forecasts met all position limits. |
| [NASA forecast extension](prediction-group-transfer/REMAINING_GROUPS_PREDICTION_RESULT.md) | Extended the retrospective check to 20 groups and retained all failed fits alongside the nine groups with usable later forecasts inside the development reference. |
| [ESA receiver and IMU method](esa-development-selection-v2/README.md) | Qualified the software path for the ESA recording format and selected development windows using receiver data and completed IMU support checks. |
| [ESA matched forecasts](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md) | Found a globe advantage on withheld positions in two complete settings on one development flight. Two other settings remain unresolved because the matched disc fits did not converge. |
| [Training-only receiver inputs](prediction-observed-development/ESA_MATCHED_SPLIT_RESULT.md) | Verified that two training lengths on the development flight can share identical prediction times while keeping later positions and covariance values out of fitting. |
| [Forecast selection before scoring](prediction-observed-development/ESA_SCORING_SEAL_RESULT.md) | Checked all 24 development task dispositions and reproduced the historical forecast choices before opening the score summary. |
| [Solver and memory checks](mixed-tangent-hybrid/ESA_DISPATCH_SCOPE_RESULT.md) | Verified agreement between two globe solvers on one development recording. [The structured receiver calculation](prediction-observed-development/STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md) avoids a dense matrix for long tracks. |
| [Receiver and ground-reference checks](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) | Checked the effect of different GPS reconstructions and compared airborne satellite measurements with two ground receivers. Shared aircraft errors remain open. |
| [Nuuk Museum one-second comparison](prediction-observed-development/ESA_NKAR_GROUND_SCORE_RESULT.md) | Matched all 120 intervals of the saved development score to an independent ground receiver. The difference projected to 2.88% of the score gap. |
| [Ground correction on later readings](prediction-observed-development/ESA_NKAR_PHASE_TRANSFER_RESULT.md) | Tested both ground receivers on identical aircraft data. Corrections learned earlier barely changed the later aircraft errors. |
| [Aircraft error budget](prediction-observed-development/ESA_NKAR_ERROR_BUDGET_RESULT.md) | Used the nearby receiver’s coverage to calculate how accurate the aircraft ranges would need to be. Actual aircraft error limits remain open. |
| [GPS antenna corrections](prediction-observed-development/ESA_NKAR_ANTENNA_RESULT.md) | Applied published satellite and ground corrections. They made little difference to the two-minute score. |
| [Aircraft antenna records](prediction-observed-development/ESA_AIRCRAFT_ANTENNA_INVENTORY.md) | Checked all three receiver headers. None identifies the shared roof antenna. |
| [Phase changes from antenna rotation](prediction-observed-development/ESA_PHASE_WINDUP_RESULT.md) | Showed that common phase cancels and bounded the contribution of tilt in an ideal antenna model. |
| [Satellite phase correction](prediction-observed-development/ESA_NKAR_PHASE_WINDUP_RESULT.md) | Applied the ideal phase correction to the fixed satellite and receiver geometry. The effect on the development score was small. |
| [Horizontal quartz alignment](prediction-observed-development/ESA_GIRAFE_DIRECTION_TRANSFER_RESULT.md) | Tested an alignment on separate earlier intervals. It left 17–18 mm/s² of northward disagreement. |
| [Motion direction and independent force coverage](prediction-observed-development/ESA_MOTION_AXIS_SUPPORT_RESULT.md) | Found that the score gap can be spanned by a north–south position error alone. The independent force recording covers the exact interval. |
| [Independent horizontal force check](prediction-observed-development/ESA_GIRAFE_HORIZONTAL_WITNESS_RESULT.md) | Found that measured disagreement and clock sensitivity exceed the signature of the constructed north–south error. |
| [Two-band GPS correction](prediction-observed-development/ESA_CARRIER_BAND_RESULT.md) | Measured the effect of using both GPS frequencies on the same 120 aircraft and ground intervals. The corrections agreed weakly. |
| [Generated-data uncertainty validation](prediction-validation-continuation/README.md) | Completed all 4,344 fits and passed a fixed coverage test across 181 simulated cases. The result applies to the simulated conditions. |
| [Simulated receiver reference scores](prediction-receiver-replay/REFERENCE_RESULT.md) | Recovered 286 scores per scenario from saved forecasts and verified the rank limits imposed by 13 unavailable seeds. |
| [Simulated receiver replay](prediction-receiver-replay/RESULT.md) | Reconstructed receiver readings for 24 saved predictions from one calibration seed and rescored them without rerunning the fits. |
| [Flight-group decision method](FLIGHT_GROUP_DECISION.md) | Tested the shape-first rule and when unfinished reference fits can no longer change the result. [Both reference methods](PREDICTION_GROUP_DECISION.md) support the stopping check. Aircraft calibration remains open. |
| [Reserved ESA groups](external-imu-data/ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md) | Found ten provisional windows across seven groups. Later checks verified [IMU continuity](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md) and [prediction times at the development cadence](external-imu-data/ESA_CONFIRMATION_CADENCE_RESULT.md) in one 20-minute slice per group. |
| [Reserved training conditions](external-imu-data/ESA_CONFIRMATION_TRAINING_PROFILE_RESULT.md) | Compared earlier GPS conditions on the seven fixed slices with the development window. All seven have weaker satellite geometry and most have more course change. |
| [Evidence and reproducibility](PAPER_DATASET.md) | Links fitted and prediction results by recording group, with frozen source and report verification. |
| [Aircraft motion evidence check](analysis-provenance/AIRCRAFT_MOTION_EVIDENCE.md) | Verifies the saved clock, tilt and paired-sensor results, including both stopped attempts. |
| [Shared GPS error and forecast accuracy](ilvis0-measurement-contribution/MATCHED_COMMON_ERROR_MARGIN_RESULT.md) | Measured how much additional shared GPS error could change the matched forecasts' accuracy and rankings. |

The [GIRAFE clock check](prediction-observed-development/ESA_GIRAFE_LEVEL1_AIRBORNE_RESULT.md) verified the reversed sign and identical GPS timestamps for the vertical export in both airborne intervals. The [tilt check](prediction-observed-development/ESA_GIRAFE_TILT_IDENTIFIABILITY_RESULT.md) measured how little orientation uncertainty could hide a horizontal force difference. The [matched NASA averages](ilvis0-measurement-contribution/PAIRED_GYRO_AVERAGED_FORCE_RESULT.md) removed the single-packet motion mismatch on the same intervals for all four candidates.

[The current plan](NEXT_STEPS.md) explains what is left. The [stationary ground experiment](STATIONARY.md) is a separate consumer-IMU project in development.
