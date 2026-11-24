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
| [Decision check for shared reference draws](FLIGHT_GROUP_DECISION.md#when-all-queries-share-the-same-reference-draws) | Verified when the remaining draws cannot change a two-stage decision on generated scores. |
| [Solver and memory checks](mixed-tangent-hybrid/ESA_DISPATCH_SCOPE_RESULT.md) | Verified agreement between two globe solvers on one development recording. [The structured receiver calculation](prediction-observed-development/STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md) avoids a dense matrix for long tracks. |
| [Receiver and ground-reference checks](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) | Checked the effect of different GPS reconstructions and compared airborne satellite measurements with two ground receivers. Shared aircraft errors remain open. |
| [Nuuk Museum one-second comparison](prediction-observed-development/ESA_NKAR_GROUND_SCORE_RESULT.md) | Matched all 120 intervals of the saved development score to an independent ground receiver. The difference projected to 2.88% of the score gap. |
| [Permanent Nuuk one-second intake](prediction-observed-development/ESA_NUUK_HIGHRATE_INTAKE_RESULT.md) | Verified a second nearby one-second station, with 520 matched times and at least 11 continuously tracked GPS satellites in each scored interval before satellite screening. |
| [Nearby Nuuk comparison](prediction-observed-development/ESA_NUUK_NEAR_STATIONS_RESULT.md) | Found 6.49 mm RMS disagreement on 100 matched seconds. The measured differences leave each station's own error and the aircraft error open. |
| [Permanent Nuuk carrier screen](prediction-observed-development/ESA_NUUK_CARRIER_SCREEN_RESULT.md) | Traced all 20 excluded seconds to the L1 Doppler check, with a common offset across satellites. The original comparison stays fixed. |
| [Nuuk Doppler offset check](prediction-observed-development/ESA_NUUK_CLOCK_AWARE_RESULT.md) | Recovered all 20 seconds in a separate check. The two stations differed by 6.54 mm RMS over the full 120 seconds. |
| [ESA instrument provenance](external-imu-data/ESA_INSTRUMENT_PROVENANCE.md) | Ties all nine archived file labels to one iMAR unit and identifies original installation measurements that could check fitted antenna offsets. |
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
| [Fixed antenna offset and the ESA score](prediction-observed-development/ESA_CARRIER_LEVER_SENSITIVITY_RESULT.md) | Used the saved gyro angles to bound how much an error in the antenna's placement could change the two-minute comparison. |
| [Antenna phase through the recorded turns](prediction-observed-development/ESA_GYRO_PHASE_TILT_RESULT.md) | Bounded the ideal phase change under three starting tilt allowances and marked where the satellite could fall below the antenna plane. |
| [Above-plane satellite support](prediction-observed-development/ESA_CARRIER_ELEVATION_SCREEN_RESULT.md) | Kept at least four satellites throughout the ESA development window, with tighter range accuracy requirements after screening. |
| [Range and motion weighting](prediction-observed-development/ESA_CARRIER_WEIGHT_TRADEOFF_RESULT.md) | Recovered much of the range margin on the screened satellite sets using a continuous model of position error between the anchors. |
| [Uncertain anchors and the new weights](prediction-observed-development/ESA_CARRIER_REWEIGHTED_BUDGET_RESULT.md) | Found that allowing one metre of error per anchor coordinate leaves no range margin in any screened case under the published example. |
| [Smooth errors in the estimated path](prediction-observed-development/ESA_CARRIER_MOTION_WITNESS_RESULT.md) | Found bounded errors that reproduce part of the score gap. The search reached its iteration limits before finding a complete example. |
| [Checks for the follow-up path solver](ESA_ERROR_POLICY.md) | Verified lower and upper score bounds against known answers, including when the optimizer stops early. |
| [Continuous trajectory error bounds](prediction-observed-development/ESA_CARRIER_CONTINUOUS_BOUND_RESULT.md) | With all satellites, the tested error limits allow at most 50.2% of the score gap. The three antenna-plane screens still leave the full gap unresolved. |
| [Independent accuracy requirements](prediction-observed-development/ESA_CARRIER_ERROR_REQUIREMENTS_RESULT.md) | Reused the saved bounds to find the covered range accuracy needed for each satellite set and tightened the bound for the 0° screen. |
| [Installed GPS on the Nuuk apron](prediction-observed-development/ESA_APRON_CARRIER_RESULT.md) | Found about 7 mm RMS range disagreement with a fixed parked position, with the recorded receiver clock corrected. |
| [Nuuk apron and museum ranges](prediction-observed-development/ESA_APRON_NKAR_RESULT.md) | Matched 216 satellite changes and found little correlation between the two receivers on the short parked interval. |
| [GPS and inertial coverage at the Nuuk stop](prediction-observed-development/ESA_APRON_IMU_OVERLAP_ACQUISITION_RESULT.md) | Verified 241 GPS epochs during a two-minute window with inertial coverage for the next ground comparison. |
| [GPS ranges during the two-minute ground check](prediction-observed-development/ESA_APRON_IMU_OVERLAP_RESULT.md) | Found weak correlation with Nuuk Museum and substantial variation in the aircraft's one-second gyro rates. |
| [Verification of the Nuuk ground results](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) | Reproduces the range and gyro summaries from the published observations and links them to one development flight. |
| [Shared GPS error across two ground stations](prediction-observed-development/ESA_TWO_STATION_SCORE_RESULT.md) | Calculates the smallest station error that could hide a shared correction as large as the airborne score gap. |
| [Galileo check of the northward displacement](prediction-observed-development/ESA_GALILEO_NORTH_WITNESS_RESULT.md) | Found about 50% larger Galileo range disagreement after adding the displacement that closes the GPS score gap. |
| [Joint GPS and Galileo path bound](prediction-observed-development/ESA_GALILEO_JOINT_BOUND_RESULT.md) | Found little leverage from the Galileo cap on the broader path bound. Two GPS satellite screens remain open under the example limits. |
| [Verification of the airborne carrier checks](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) | Recomputes the two-station cases, Galileo residuals and joint bound summaries from the saved evidence. |

The [GIRAFE clock check](prediction-observed-development/ESA_GIRAFE_LEVEL1_AIRBORNE_RESULT.md) verified the reversed sign and identical GPS timestamps for the vertical export in both airborne intervals. The [tilt check](prediction-observed-development/ESA_GIRAFE_TILT_IDENTIFIABILITY_RESULT.md) measured how little orientation uncertainty could hide a horizontal force difference. The [matched NASA averages](ilvis0-measurement-contribution/PAIRED_GYRO_AVERAGED_FORCE_RESULT.md) removed the single-packet motion mismatch on the same intervals for all four candidates.

The [RF04 source check](ilvis0-measurement-contribution/NCAR_RF04_INTAKE.md) identified separate aircraft attitude, GPS and pressure channels for one IceBridge flight. The flight data are still pending.

[The current plan](NEXT_STEPS.md) explains what is left. The [stationary ground experiment](STATIONARY.md) is a separate consumer-IMU project in development.
