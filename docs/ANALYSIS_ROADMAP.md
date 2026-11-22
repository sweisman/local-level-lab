# Analysis roadmap

## Where the project stands

<!-- current-status:start -->
**53 of 53 selected stretches favored the globe with the specified background field.** The tested flat disc was preferred in 0 stretches. 0 lacked a consistent preference.
The [verified results](CURRENT_STATUS.md) give the model and repeat counts.
<!-- current-status:end -->

NASA's selected-stretch comparison is numerically complete. The later NASA forecasts and the ESA forecasts use development recordings. Seven separate ESA groups each have one timing-verified 20-minute slice. They have supplied zero confirmation fits. [Prediction evidence](PAPER_DATASET.md#prediction-evidence-kept-separately) · [ESA timing](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md)

## Current milestones and finish line

1. **Constrain the errors that can change a comparison.** Assess GPS errors shared by the aircraft's receivers and uncertainty in inertial measurements and fitted calibration. The nearby high-rate Nuuk reference is pending. The [current error budget](prediction-observed-development/ESA_REFERENCE_ERROR_BUDGET.md) states the limits that measurements would need to support.
2. **Qualify and freeze the full prediction rule.** Specify the training interval, withheld positions, matched model and processing cases, accuracy checks, and treatment of failures. Use independent known-answer cases and aircraft-relevant errors to test the rule. Any allowed evidence that shares observations stays in the same flight group.
3. **Test the reserved ESA flight groups.** Freeze their selection, error model and comparison rules first. Report model preference, absolute prediction accuracy and calibrated uncertainty separately. Keep missing or inadequate groups in the count. Seven reserved groups provide a transfer test with [limited coverage resolution](PREDICTION_GROUP_COUNT.md).
4. **Verify the evidence.** Preserve originals, charged work, incomplete results and source hashes. Link each public claim to the verified report that supports it. Publish enough evidence to reproduce the result and state what remains unresolved.

## Dependency-ordered backlog

| ID | Priority | Status | Work or evidence |
| --- | --- | --- | --- |
| F01 | Foundation | Complete | [Record provenance and dependence](PROVENANCE_VERIFICATION.md) for the NASA and ESA groups. |
| F02 | Foundation | Complete | [Reserve seven separate ESA groups](external-imu-data/README.md) for confirmation. Use recording 187 for development. |
| C01 | First | Complete | Verify the basic [motion and channel calculations](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md). |
| C02 | First | Aircraft error bounds open | [Sensitivity to Doppler and shared receiver errors](prediction-observed-development/ESA_DOPPLER_CONTRAST_RESULT.md) has been measured on the development flight. An error common to all receivers could still affect the shape score. |
| C03 | First | Two matched development settings complete | [Matched forecasting](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md) favored globe in both complete settings. Two settings remain unresolved. Test matched forecasts under a qualified aircraft error model. |
| C04 | First | Force-only result unresolved | [Force-only sensitivity](ilvis0-measurement-contribution/SHARED_FORCE_WITNESS_RESULT.md) leaves shape open. The [independent aircraft motion file](ilvis0-measurement-contribution/NCAR_RF04_INTAKE.md) remains pending. |
| V01 | First | Software controls passed | [All 24 known-answer forecast controls](ilvis0-near-zero-forecast-controls/README.md) passed within their fixed allowance. |
| V02 | First | Retrospective accuracy checked | All 104 saved NASA forecasts tested [meet the fixed position limits](prediction-group-transfer/ACCURACY_MARGIN_RESULT.md). ESA development coverage changes across GPS solutions. Check absolute accuracy on independent flights. |
| L01 | During qualification | Faster globe solver checked on one recording | [Paired solver results](mixed-tangent-hybrid/ESA_DISPATCH_SCOPE_RESULT.md) match on the development window. The wide method remains the reference for other observed recordings and the disc. |
| L02 | During qualification | Linear-memory scoring checked | The [structured receiver operator](prediction-observed-development/STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md) agrees with dense controls. Aircraft uncertainty remains open. |
| E01 | Before confirmation | Timing passed in seven groups | The [receiver screen](external-imu-data/ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md) found ten provisional windows. [One 20-minute slice per group](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md) has continuous timestamps. |
| E02 | First | Aircraft error model open | [Matched ground references](prediction-observed-development/ESA_GROUND_COMMON_PRODUCTS_RESULT.md) help test shared GPS effects. The remaining uncertainty includes errors at the airborne antenna, absolute position and faster motion. |
| G01 | Development | Descriptive gyro check complete | [Raw pitch-rate comparisons](ilvis0-gyro-companion-v2/INTERPRETATION.md) relate measured turning to predicted rates, with aircraft motion and mounting effects still mixed in. |
| U01 | Before publication | Development evidence verified | The [public evidence tables](PAPER_DATASET.md) track reused observations, numerical failures and the distinction between development and confirmation. |
| U02 | Before a calibrated claim | Aircraft calibration open | The [two-stage group decision](PREDICTION_GROUP_DECISION.md) has software checks. Qualify per-group uncertainty and test the full decision procedure. |
| U03 | Development | Simulated validation passed | The [recorded continuation](VALIDATION_CONTINUATION.md) finished the 181-case generated study under its original rules. |
| R01 | Later | Planned | [Estimate the background angular field freely](ROTATION_FIELD.md). |
| R02 | Later | After R01 | Test whether field measurement is precise enough to distinguish solar from sidereal rate. |
| S01 | Later | Separate work | Continue the [stationary experiment](STATIONARY.md) and [secondary data leads](external-imu-data/README.md) under their own rules. |
| D01 | Supporting | Open | Document exact instrument corrections where sources allow. Keep the tested processing assumptions visible. [Instrument guide](ILVIS0.md#instrument-quality) |

## Execution order and completion checks

Use a separate recorded allowance for each new study. Bind selection, inputs, source, environment, methods, recovery limits and observable exit conditions before launch. Preserve sealed work and charges. Pass software qualification before dependent observed fits. Use receiver-only data for eligibility and keep the reserved sensor outcomes unopened until confirmation rules are frozen. [Reproduction and study operation](REPRODUCIBILITY.md) · [Runtime status](../analysis/STATUS.md)

## Development record

[Detailed study record](STUDY_RECORD.md) · [Earlier roadmap and development checks](RESEARCH_ROADMAP_HISTORY.md) · [Plain-language next steps](NEXT_STEPS.md)
