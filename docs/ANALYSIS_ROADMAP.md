# Analysis roadmap

## Where the project stands

<!-- current-status:start -->
**53 of 53 selected stretches favored the globe with the specified background field.** The tested flat disc was preferred in 0 stretches. 0 lacked a consistent preference.
The [verified results](CURRENT_STATUS.md) give the model and repeat counts.
<!-- current-status:end -->

NASA's selected-stretch comparison is numerically complete. The later NASA forecasts and the ESA forecasts use development recordings. Seven separate ESA groups each have one timing-verified 20-minute slice. They have supplied zero confirmation fits. [Prediction evidence](PAPER_DATASET.md#prediction-evidence-kept-separately) · [ESA timing](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md)

The next NASA motion check awaits RF04. ESA confirmation awaits independently supported aircraft-error limits, including evidence on platform orientation and the shared roof antenna. The two development tracks can resume separately when their records become available. [RF04 intake](ilvis0-measurement-contribution/NCAR_RF04_INTAKE.md) · [ESA instrument provenance](external-imu-data/ESA_INSTRUMENT_PROVENANCE.md)

The Nuuk Museum receiver covered all 120 intervals in the development comparison. With the full satellite set and the other example limits fixed, the covered aircraft range error would need to stay below about 2.10 mm RMS. The aircraft antenna, tracking, absolute position and inertial errors still need independent constraints. [Required error bounds](prediction-observed-development/ESA_CARRIER_ERROR_REQUIREMENTS_RESULT.md)

## Current milestones and finish line

1. **Constrain the errors that can change a comparison.** Assess GPS errors shared by the aircraft's receivers and uncertainty in inertial measurements and fitted calibration. The [current error budget](prediction-observed-development/ESA_NKAR_ERROR_BUDGET_RESULT.md) states the limits that measurements would need to support.
2. **Qualify and freeze the full prediction rule.** Specify the training interval, withheld positions, matched model and processing cases, accuracy checks, and treatment of failures. Use independent known-answer cases and aircraft-relevant errors to test the rule. Any allowed evidence that shares observations stays in the same flight group.
3. **Test the reserved ESA flight groups.** Freeze their selection, error model and comparison rules first. Report model preference, absolute prediction accuracy and calibrated uncertainty separately. Keep missing or inadequate groups in the count. Seven reserved groups provide a transfer test with [limited coverage resolution](PREDICTION_GROUP_COUNT.md).
4. **Verify the evidence.** Preserve originals, charged work, incomplete results and source hashes. Link each public claim to the verified report that supports it. Publish enough evidence to reproduce the result and state what remains unresolved.

## What would advance the next test

| Needed evidence | What the development checks tell us |
| --- | --- |
| An independent check on the GPS error shared by the aircraft receivers | The receivers share one roof antenna. The two ground stations constrain some shared satellite errors, but their agreement gives no upper bound on errors local to the aircraft. A useful check would measure or bound the aircraft antenna and tracking errors over the scored interval. [Two-station comparison](prediction-observed-development/ESA_TWO_STATION_SCORE_RESULT.md) |
| Time-matched horizontal motion and instrument orientation | The two-minute comparison covered a 401 m climb. A north–south path change can span the saved score gap while changing the horizontal force by just 0.37–0.71 mm/s² RMS. Both the quartz disagreement and the effect of a 0.1-second clock shift are larger. A timestamped platform-state and orientation record would help assess what the separate sensor can resolve. [Horizontal force comparison](prediction-observed-development/ESA_GIRAFE_HORIZONTAL_WITNESS_RESULT.md) · [Flight and instrument context](external-imu-data/ESA_GIRAFE_187.md#aircraft-motion-and-platform-state-in-the-two-minute-check) |
| A justified joint bound on calibration and forecast errors | For the saved zero-field forecast pair, the compact calculation pins the best uniform error allowance at about 2.25 cm per coordinate under the existing assumptions. The targeted earlier GPS checks leave that limit unchanged. Independent calibration limits or evidence about how errors vary together across the forecast would change the calculation. [Compact bound](prediction-observed-development/ESA_COMPACT_FORECAST_MARGIN_RESULT.md) · [Follow-up](prediction-observed-development/ESA_CONTRAST_SCORE_ALIGNED_RESULT.md) |

The numbers above refer to specific development comparisons. The [training profiles](external-imu-data/ESA_CONFIRMATION_TRAINING_PROFILE_RESULT.md) show differences in satellite geometry and motion on the reserved flights. Any error model used for confirmation must cover those conditions.

## Dependency-ordered backlog

| ID | Priority | Status | Work or evidence |
| --- | --- | --- | --- |
| F01 | Foundation | Complete | [Record provenance and dependence](PROVENANCE_VERIFICATION.md) for the NASA and ESA groups. |
| F02 | Foundation | Complete | [Reserve seven separate ESA groups](external-imu-data/README.md) for confirmation. Use recording 187 for development. All eight groups [share one identified instrument](external-imu-data/ESA_INSTRUMENT_PROVENANCE.md). |
| C01 | First | Complete | Verify the basic [motion and channel calculations](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md). |
| C02 | First | Aircraft error bounds open | A constructed [north–south position error](prediction-observed-development/ESA_MOTION_AXIS_SUPPORT_RESULT.md) spans the GPS score gap but raises [Galileo range disagreement](prediction-observed-development/ESA_GALILEO_NORTH_WITNESS_RESULT.md) by about half. The [broader joint bound](prediction-observed-development/ESA_GALILEO_JOINT_BOUND_RESULT.md) still leaves two screened cases open under the example limits. Independent motion and platform orientation remain open. |
| C03 | First | Two matched development settings complete | [Matched forecasting](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md) favored globe in both complete settings. Two settings remain unresolved. Test matched forecasts under a qualified aircraft error model. |
| C04 | First | Force-only result unresolved | [Averaged force directions](ilvis0-measurement-contribution/PAIRED_GYRO_AVERAGED_FORCE_RESULT.md) clear the paired logged-gyro budget for all four candidates. The [RF04 source check](ilvis0-measurement-contribution/NCAR_RF04_INTAKE.md) identified separate aircraft attitude, GPS and pressure channels for comparison. The recording and an independent upper limit on motion remain outstanding. |
| V01 | First | Software controls passed | [Known-answer forecasts](ilvis0-near-zero-forecast-controls/README.md) passed. Development replays verified [earlier-only receiver inputs](prediction-observed-development/ESA_MATCHED_SPLIT_RESULT.md) and [selection before scoring](prediction-observed-development/ESA_SCORING_SEAL_RESULT.md). |
| V02 | First | Retrospective accuracy checked | The [matched NASA forecasts](ilvis0-measurement-contribution/MATCHED_COMMON_ERROR_MARGIN_RESULT.md) reached their accuracy limit with 1.69–8.22 m of added shared GPS error, while their first model-ranking ties needed 39.01–62.74 m. Nine of the 20 [transfer groups](prediction-group-transfer/REMAINING_GROUPS_PREDICTION_RESULT.md) supplied a passing later-cut fit. Independent forecast accuracy remains open. |
| L01 | During qualification | Faster globe solver checked on one recording | [Paired solver results](mixed-tangent-hybrid/ESA_DISPATCH_SCOPE_RESULT.md) match on the development window. The wide method remains the reference for other observed recordings and the disc. |
| L02 | During qualification | Linear-memory scoring checked | The [structured receiver operator](prediction-observed-development/STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md) agrees with dense controls. Aircraft uncertainty remains open. |
| E01 | Before confirmation | Timing and earlier conditions verified | All seven fixed slices support [both training lengths](external-imu-data/ESA_CONFIRMATION_CADENCE_RESULT.md) with the same withheld reports. The [public verifier](external-imu-data/ESA_CONFIRMATION_TRAINING_PROFILE_RESULT.md#verify-from-the-public-files) checks those layouts and the saved comparisons of satellite geometry and course change. |
| E02 | First | Aircraft error bounds open | The [accuracy requirements replay](prediction-observed-development/ESA_CARRIER_ERROR_REQUIREMENTS_RESULT.md) puts the covered aircraft range threshold at about 2.10 mm RMS under the other example caps. A [separate Doppler check](prediction-observed-development/ESA_NUUK_CLOCK_AWARE_RESULT.md) recovered all 120 seconds and found 6.54 mm RMS disagreement between the two Nuuk stations. The original [100-second comparison](prediction-observed-development/ESA_NUUK_NEAR_STATIONS_RESULT.md) remains available. Upper bounds on station and aircraft-specific errors remain open. |
| G01 | Development | Matched-field gyro diagnostic complete | The [group-weighted pitch comparison](ilvis0-gyro-companion-v2/MATCHED_GROUP_RESULT.md) favors globe across the tested poses at the specified field for both shapes. The zero-field ranking can change. Independent aircraft motion and mounting effects remain open. |
| U01 | Before publication | Development evidence verified | The [evidence tables](PAPER_DATASET.md) track reused observations and numerical failures. The [carrier verifier](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) checks both Nuuk ground intervals, the two-station cases and the airborne Galileo results. The [motion verifier](analysis-provenance/AIRCRAFT_MOTION_EVIDENCE.md) checks the clock, tilt and paired-sensor studies. |
| U02 | Before a calibrated claim | Aircraft calibration open | The [simulation reference replay](prediction-receiver-replay/REFERENCE_RESULT.md) recovered 286 scores per scenario and kept 13 unavailable seeds. The [shared-reference work check](FLIGHT_GROUP_DECISION.md#when-all-queries-share-the-same-reference-draws) now detects when unfinished draws cannot change either stage. The [two-stage rule](PREDICTION_GROUP_DECISION.md) still needs an aircraft error model and independent testing. |
| U03 | Development | Simulated validation passed | The [recorded continuation](VALIDATION_CONTINUATION.md) finished the 181-case generated study under its original rules. |
| R01 | Later | Planned | [Estimate the background angular field freely](ROTATION_FIELD.md). |
| R02 | Later | After R01 | Test whether field measurement is precise enough to distinguish solar from sidereal rate. |
| S01 | Later | Separate work | Continue the [stationary experiment](STATIONARY.md) and [secondary data leads](external-imu-data/README.md) under their own rules. |
| D01 | Supporting | Open | Document exact instrument corrections where sources allow. Keep the tested processing assumptions visible. [Instrument guide](ILVIS0.md#instrument-quality) |

## Execution order and completion checks

Use a separate recorded allowance for each new study. Bind selection, inputs, source, environment, methods, recovery limits and observable exit conditions before launch. Preserve sealed work and charges. Pass software qualification before dependent observed fits. Use receiver-only data for eligibility and keep the reserved sensor outcomes unopened until confirmation rules are frozen. [Reproduction and study operation](REPRODUCIBILITY.md) · [Runtime status](../analysis/STATUS.md)

### Resume from the saved evidence

- Start with the [verification commands](PAPER_DATASET.md#verify-the-public-evidence). They check the 53-stretch NASA baseline, the saved forecast comparisons, the motion and carrier evidence, and the exact layouts for both training lengths in all seven reserved ESA groups.
- For the ESA development flight, the [separate Doppler check](prediction-observed-development/ESA_NUUK_CLOCK_AWARE_RESULT.md) now provides all 120 matched seconds for testing shared and station-local errors. A [timestamped platform-state and orientation record](external-imu-data/ESA_GIRAFE_187.md#aircraft-motion-and-platform-state-in-the-two-minute-check) remains outstanding. Aircraft antenna errors and forecast uncertainty also need independent bounds.
- For the NASA force-only comparison, the [RF04 intake](ilvis0-measurement-contribution/NCAR_RF04_INTAKE.md) is tested and awaits the original flight file. Its one-second estimates can check changes between reports. An upper bound on faster aircraft motion still needs separate evidence.
- After those development checks, qualify the aircraft error model and freeze the prediction, physical accuracy and decision rules before scoring any reserved group. Keep numerical stops and abstentions in the denominator. Verify and publish the complete evidence with its source dependencies.

## Development record

[Detailed study record](STUDY_RECORD.md) · [Earlier roadmap and development checks](RESEARCH_ROADMAP_HISTORY.md) · [Plain-language next steps](NEXT_STEPS.md)
