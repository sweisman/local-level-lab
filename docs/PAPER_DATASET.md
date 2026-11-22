# Evidence dataset

The public evidence separates the original NASA comparison, later development forecasts, and reserved ESA confirmation material. It preserves failures and shows where recordings share observations.

| Evidence | What it includes |
| --- | --- |
| [Frozen NASA development snapshot](paper-development-dataset-v2/README.md) | 53 stretches, 318 latest model and processing comparisons, and 791 numerical-history records. |
| [NASA evidence by recording group](analysis-provenance/NASA_GROUP_EVIDENCE.md) | 27 conservative groups, with links to fitted results, withheld forecasts and paired-sensor checks. |
| [ESA development forecast index](analysis-provenance/ESA_GROUP_EVIDENCE.md) | Receiver-row reuse across forecast windows on one development flight. |
| [ESA ground reference evidence](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) | Timing, range and accuracy checks for that same development flight. |
| [Reserved ESA groups](external-imu-data/ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md) | Ten provisional windows across seven groups. [One 20-minute slice per group](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md) passed the timestamp check. Zero groups have been scored for confirmation. |

## How the 53 stretches cluster

Eleven groups contain one selected stretch, six groups contain two, and ten groups contain three. Groups keep overlapping and shared evidence together. The group count leaves hardware and systematic errors across flights open. [Grouping and source verification](PROVENANCE_VERIFICATION.md)

Under the original two processing assumptions the specified-field globe has lower fitted cost on all 53 stretches. Holding both shapes at zero field gives a different result. All stretches favor globe in 17 groups, all favor disc in five, and outcomes vary within the remaining five. [Zero-field comparison by group](analysis-provenance/NASA_ZERO_FIELD_BY_GROUP.md)

## Prediction evidence kept separately

- **NASA matched forecasts.** The four-group audit verified 15 of 16 forecasts. At the same specified field, globe had lower 3D error on all four groups. Three specified-field globe forecasts met all fixed accuracy limits. [Matched report](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md)
- **NASA forecast extension.** The 20-group study completed 80 planned fits. Nine groups supplied later forecasts that met the fixed reference and physical screen. Eleven had no usable later-cut fit. [Forecast extension](prediction-group-transfer/REMAINING_GROUPS_PREDICTION_RESULT.md)
- **ESA matched forecasts.** Two complete settings favored globe on one development flight. Two settings remain unresolved. The fit used earlier positions, and the later positions were scored against the resulting forecasts. [ESA comparison](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md)

The NASA forecasts use the original archive, and the ESA forecasts above use a single development flight. Qualification of an aircraft error model, independent replication and calibrated decisions remain open.

## Verify the public evidence

Run these commands from the repository root. They read saved evidence and verify published results without refitting. [Archive and environment instructions](REPRODUCIBILITY.md)

~~~~sh
~/venv/bin/python docs/build_current_status.py --check
~/venv/bin/python docs/paper-development-dataset-v2/build_dataset.py --check-public
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_group_evidence check
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_confirmation_receiver_inventory report
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_confirmation_timing report
~~~~

The [earlier dataset guide](EVIDENCE_DATASET_HISTORY.md) preserves detailed source counts, numerical environments and subsequent checks. [Study index](STUDIES.md) · [Next steps](NEXT_STEPS.md)
