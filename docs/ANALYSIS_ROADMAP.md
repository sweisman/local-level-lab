# Analysis roadmap

## Where the project stands

<!-- current-status:start -->
**53 of 53 selected stretches favored the globe with the specified background field.** The tested flat disc was preferred in 0 stretches. 0 lacked a consistent preference.
The [verified results](CURRENT_STATUS.md) give the model and repeat counts.
<!-- current-status:end -->

NASA's selected-stretch comparison is numerically complete. The later NASA forecasts and the ESA forecasts use development recordings. Seven separate ESA groups each have one timing-verified 20-minute slice. They have supplied zero confirmation fits. [Prediction evidence](PAPER_DATASET.md#prediction-evidence-kept-separately) · [ESA timing](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md)

The Nuuk Museum receiver covered all 120 intervals in the development comparison. Its coverage allows about 0.96 mm RMS in the covered aircraft range directions under the example position and motion assumptions. The aircraft antenna, tracking, absolute position and inertial errors still need independent constraints. [Required error bounds](prediction-observed-development/ESA_NKAR_ERROR_BUDGET_RESULT.md)

## Current milestones and finish line

1. **Constrain the errors that can change a comparison.** Assess GPS errors shared by the aircraft's receivers and uncertainty in inertial measurements and fitted calibration. The [current error budget](prediction-observed-development/ESA_NKAR_ERROR_BUDGET_RESULT.md) states the limits that measurements would need to support.
2. **Qualify and freeze the full prediction rule.** Specify the training interval, withheld positions, matched model and processing cases, accuracy checks, and treatment of failures. Use independent known-answer cases and aircraft-relevant errors to test the rule. Any allowed evidence that shares observations stays in the same flight group.
3. **Test the reserved ESA flight groups.** Freeze their selection, error model and comparison rules first. Report model preference, absolute prediction accuracy and calibrated uncertainty separately. Keep missing or inadequate groups in the count. Seven reserved groups provide a transfer test with [limited coverage resolution](PREDICTION_GROUP_COUNT.md).
4. **Verify the evidence.** Preserve originals, charged work, incomplete results and source hashes. Link each public claim to the verified report that supports it. Publish enough evidence to reproduce the result and state what remains unresolved.

## Dependency-ordered backlog

| ID | Priority | Status | Work or evidence |
| --- | --- | --- | --- |
| F01 | Foundation | Complete | [Record provenance and dependence](PROVENANCE_VERIFICATION.md) for the NASA and ESA groups. |
| F02 | Foundation | Complete | [Reserve seven separate ESA groups](external-imu-data/README.md) for confirmation. Use recording 187 for development. |
| C01 | First | Complete | Verify the basic [motion and channel calculations](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md). |
| C02 | First | Aircraft error bounds open | A [north–south position error](prediction-observed-development/ESA_MOTION_AXIS_SUPPORT_RESULT.md) alone can span the score gap. At most 0.181 mrad of [tilt per force average](prediction-observed-development/ESA_GIRAFE_TILT_IDENTIFIABILITY_RESULT.md) can hide its direction change. The [GIRAFE clock check](prediction-observed-development/ESA_GIRAFE_LEVEL1_AIRBORNE_RESULT.md) aligned two vertical exports. Independent horizontal motion and platform orientation remain open. |
| C03 | First | Two matched development settings complete | [Matched forecasting](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md) favored globe in both complete settings. Two settings remain unresolved. Test matched forecasts under a qualified aircraft error model. |
| C04 | First | Force-only result unresolved | [Averaged force directions](ilvis0-measurement-contribution/PAIRED_GYRO_AVERAGED_FORCE_RESULT.md) clear the paired logged-gyro budget for all four candidates, resolving the single-packet mismatch under the averaging assumptions. An independent motion limit remains open. The pending [RF04 file](ilvis0-measurement-contribution/NCAR_RF04_INTAKE.md) could check whole-second motion separately on the 2011 flight. |
| V01 | First | Software controls passed | [Known-answer forecasts](ilvis0-near-zero-forecast-controls/README.md) passed. Development replays verified [earlier-only receiver inputs](prediction-observed-development/ESA_MATCHED_SPLIT_RESULT.md) and [selection before scoring](prediction-observed-development/ESA_SCORING_SEAL_RESULT.md). |
| V02 | First | Retrospective accuracy checked | The [matched NASA forecasts](ilvis0-measurement-contribution/MATCHED_COMMON_ERROR_MARGIN_RESULT.md) reached their accuracy limit with 1.69–8.22 m of added shared GPS error, while their first model-ranking ties needed 39.01–62.74 m. Nine of the 20 [transfer groups](prediction-group-transfer/REMAINING_GROUPS_PREDICTION_RESULT.md) supplied a passing later-cut fit. Independent forecast accuracy remains open. |
| L01 | During qualification | Faster globe solver checked on one recording | [Paired solver results](mixed-tangent-hybrid/ESA_DISPATCH_SCOPE_RESULT.md) match on the development window. The wide method remains the reference for other observed recordings and the disc. |
| L02 | During qualification | Linear-memory scoring checked | The [structured receiver operator](prediction-observed-development/STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md) agrees with dense controls. Aircraft uncertainty remains open. |
| E01 | Before confirmation | Timing and earlier conditions verified | All seven fixed slices support [both training lengths](external-imu-data/ESA_CONFIRMATION_CADENCE_RESULT.md). Their [earlier receiver profiles](external-imu-data/ESA_CONFIRMATION_TRAINING_PROFILE_RESULT.md) show weaker satellite geometry and more course change in most slices than the development split. |
| E02 | First | Aircraft error bounds open | The [accuracy requirements replay](prediction-observed-development/ESA_CARRIER_ERROR_REQUIREMENTS_RESULT.md) puts the covered range threshold at about 2.10 mm RMS under the other example caps. The [two-minute ground check](prediction-observed-development/ESA_APRON_IMU_OVERLAP_RESULT.md) found little shared GPS error and substantial variation in the recorded gyro rates. Independent limits on airborne errors remain open. |
| G01 | Development | Matched-field gyro diagnostic complete | The [group-weighted pitch comparison](ilvis0-gyro-companion-v2/MATCHED_GROUP_RESULT.md) favors globe across the tested poses at the specified field for both shapes. The zero-field ranking can change. Independent aircraft motion and mounting effects remain open. |
| U01 | Before publication | Development evidence verified | The [evidence tables](PAPER_DATASET.md) track reused observations and numerical failures. The [ground-reference verifier](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) reproduces scores and antenna corrections. The [motion verifier](analysis-provenance/AIRCRAFT_MOTION_EVIDENCE.md) checks the recent clock, tilt and paired-sensor studies. |
| U02 | Before a calibrated claim | Aircraft calibration open | The [simulation reference replay](prediction-receiver-replay/REFERENCE_RESULT.md) recovered 286 scores per scenario and kept 13 unavailable seeds. The [two-stage rule](PREDICTION_GROUP_DECISION.md) still needs an aircraft error model and independent testing. |
| U03 | Development | Simulated validation passed | The [recorded continuation](VALIDATION_CONTINUATION.md) finished the 181-case generated study under its original rules. |
| R01 | Later | Planned | [Estimate the background angular field freely](ROTATION_FIELD.md). |
| R02 | Later | After R01 | Test whether field measurement is precise enough to distinguish solar from sidereal rate. |
| S01 | Later | Separate work | Continue the [stationary experiment](STATIONARY.md) and [secondary data leads](external-imu-data/README.md) under their own rules. |
| D01 | Supporting | Open | Document exact instrument corrections where sources allow. Keep the tested processing assumptions visible. [Instrument guide](ILVIS0.md#instrument-quality) |

## Execution order and completion checks

Use a separate recorded allowance for each new study. Bind selection, inputs, source, environment, methods, recovery limits and observable exit conditions before launch. Preserve sealed work and charges. Pass software qualification before dependent observed fits. Use receiver-only data for eligibility and keep the reserved sensor outcomes unopened until confirmation rules are frozen. [Reproduction and study operation](REPRODUCIBILITY.md) · [Runtime status](../analysis/STATUS.md)

## Development record

[Detailed study record](STUDY_RECORD.md) · [Earlier roadmap and development checks](RESEARCH_ROADMAP_HISTORY.md) · [Plain-language next steps](NEXT_STEPS.md)
