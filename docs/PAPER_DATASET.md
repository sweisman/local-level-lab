# Evidence dataset

The fitted NASA comparison favors the globe with the specified background
field on all **53 selected stretches**, organized into **27 recording groups**.
At the same specified field for both shapes, globe forecasts had lower
withheld position error on all four NASA groups in the matched audit.
The specified-field globe met all fixed position limits in three groups.
A separate ESA development flight
favored globe in both complete settings, with two settings unresolved.

These findings describe the tested models and recordings. Independent
flight confirmation and calibrated uncertainty remain open. The
tables below preserve unsuccessful comparisons and show where recordings
share observations. [NASA forecasts](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md) ·
[ESA forecasts](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md)

| Evidence | What it includes |
| --- | --- |
| [Frozen NASA development snapshot](paper-development-dataset-v2/README.md) | 53 stretches, 318 latest model and processing comparisons, and 791 numerical-history records. |
| [NASA evidence by recording group](analysis-provenance/NASA_GROUP_EVIDENCE.md) | 27 conservative groups, with links to fitted results, withheld forecasts and paired-sensor checks. |
| [ESA development forecast index](analysis-provenance/ESA_GROUP_EVIDENCE.md) | Receiver-row reuse across forecast windows on one development flight. |
| [ESA ground reference evidence](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) | Reproducible timing, range, antenna and error-budget checks for that same development flight, including both ground intervals and the airborne GPS–Galileo comparisons. |
| [Nearby Nuuk ground comparison](prediction-observed-development/ESA_NUUK_NEAR_STATIONS_RESULT.md) | 994 matched range changes from the two Nuuk stations, with a three-station comparison and conditional bounds on shared range error. |
| [Nuuk Doppler offset check](prediction-observed-development/ESA_NUUK_CLOCK_AWARE_RESULT.md) | 1,236 matched range changes spanning all 120 seconds in a separate receiver-quality check. |
| [Aircraft motion evidence](analysis-provenance/AIRCRAFT_MOTION_EVIDENCE.md) | Verify the ESA clock and tilt checks and the two distinct paired NASA flights, including the source correction. |
| [RF04 evidence chain](analysis-provenance/RF04_EVIDENCE.md) | Verifies seven development checks on one stretch, from the original recorder comparison to the remaining acceleration disagreement. |
| [ESA antenna offset sensitivity](prediction-observed-development/ESA_CARRIER_LEVER_SENSITIVITY_RESULT.md) | Bounds how much a fixed error in antenna placement can change the saved two-minute score. |
| [ESA installed antenna sensitivity](prediction-observed-development/ESA_INSTALLED_PATTERN_RESULT.md) | Calculates the minimum angular response slope that could explain the saved score gap under the stated motion assumptions. |
| [Reserved ESA groups](external-imu-data/ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md) | Seven groups each have a timing-verified slice with two training lengths. The [preflight](external-imu-data/ESA_CONFIRMATION_PREFLIGHT.md) verifies the exact cohort and can check the future frozen plan. Zero groups have been scored for confirmation. |

## How the 53 stretches cluster

Eleven groups contain one selected stretch, six groups contain two, and ten groups contain three. Groups keep overlapping and shared evidence together. The group count leaves hardware and systematic errors across flights open. [Grouping and source verification](PROVENANCE_VERIFICATION.md)

Under the original two processing assumptions the specified-field globe has lower fitted cost on all 53 stretches. Holding both shapes at zero field gives a different result. All stretches favor globe in 17 groups, all favor disc in five, and outcomes vary within the remaining five. [Zero-field comparison by group](analysis-provenance/NASA_ZERO_FIELD_BY_GROUP.md)

## Prediction evidence kept separately

- **NASA matched forecasts.** The four-group audit verified 15 of 16 forecasts. At the same specified field, globe had lower 3D error on all four groups. Three specified-field globe forecasts met all fixed accuracy limits. Those limits were more sensitive than their model rankings to additional shared GPS error. [Matched report](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md) · [Shared-error margins](ilvis0-measurement-contribution/MATCHED_COMMON_ERROR_MARGIN_RESULT.md)
- **NASA forecast extension.** The 20-group study completed 80 planned fits. Nine groups supplied later forecasts that met the fixed reference and physical screen. Eleven had no usable later-cut fit. [Forecast extension](prediction-group-transfer/REMAINING_GROUPS_PREDICTION_RESULT.md)
- **ESA matched forecasts.** Two complete settings favored globe on one development flight. Two settings remain unresolved. The fit used earlier positions, and the later positions were scored against the resulting forecasts. [ESA comparison](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md)

The NASA forecasts use the original archive, and the ESA forecasts above use a single development flight. The seven reserved ESA groups share its inertial instrument. Their calibration can carry errors across flights. Qualification of an aircraft error model, independent flight replication and calibrated decisions remain open. [ESA instrument provenance](external-imu-data/ESA_INSTRUMENT_PROVENANCE.md)

## Verify the public evidence

From the repository root, first verify the public counts and both frozen
snapshots. These two checks require only the public files and ordinary
Python. They take no flight downloads or model fitting.

```sh
~/venv/bin/python docs/build_current_status.py --check
~/venv/bin/python docs/paper-development-dataset-v2/build_dataset.py --check-public
```

The remaining commands verify the group assignments and the deeper
forecast, motion and reservation evidence. They read the saved material
without refitting. [Archive and environment instructions](REPRODUCIBILITY.md)

~~~~sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  ~/venv/bin/python -m lll.ilvis0_group_evidence_current check
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_group_evidence check
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  ~/venv/bin/python -m lll.esa_ground_reference_evidence check --version 7
env PYTHONPATH=analysis ~/venv/bin/python -m lll.aircraft_motion_evidence
env PYTHONPATH=analysis ~/venv/bin/python -m lll.rf04_evidence
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_confirmation_receiver_inventory report
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_confirmation_timing report
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_confirmation_evidence
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_confirmation_preflight
~~~~

The [earlier dataset guide](EVIDENCE_DATASET_HISTORY.md) preserves detailed source counts, numerical environments and subsequent checks. [Study index](STUDIES.md) · [Next steps](NEXT_STEPS.md)
