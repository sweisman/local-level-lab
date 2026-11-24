# Additional airborne data

The NASA archive supplies the completed 53-stretch comparison. ESA/DTU supplies a separate survey program for testing whether the method carries over to another aircraft and instrument. Wuhan University supplies a separate development lead. Each source has its own eligibility rules.

| Source | Observations | Status |
| --- | --- | --- |
| [ESA AirQuantumGrav and Green Quantum](https://doi.org/10.57780/esa-58c58c5) | About 300 Hz iMAR inertial measurement unit (IMU) records and separate GPS receiver exports. | One development recording has been fitted. Seven other flight groups are reserved for confirmation. |
| [Wuhan University SmartPNT-POS](https://www.kaggle.com/datasets/fengzhusgg/smartpnt-pos) | The inspected airborne sample has 115,696 IMU observations over 19.28 minutes and a separate raw GNSS file. | Independent receiver positions and eligibility still need work. |
| [Wuhan long-record lead](smartpnt-long-record-report.json) | A header and end records indicate a 20.85-hour span at 600 Hz. | Interior continuity, stationary conditions, and mounting remain unverified. |

## ESA development and reserved flights

Development recording 187 contains approximately 8.49 hours of IMU samples from one survey flight. The [full-motion selection](../esa-development-selection-v2/README.md) admits two runs totaling 393.4 minutes under its receiver and IMU support rules. The measurements include turns and climbs. A slower flight can cover the distance needed to test curvature over a longer window, while persistent instrument errors still need separate assessment.

On that development flight, [two complete matched settings](../prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md) favor globe on withheld GPS positions. Two settings remain unresolved. Aircraft uncertainty is still open. [Forecast reuse by receiver row](../analysis-provenance/ESA_GROUP_EVIDENCE.md) · [Ground reference checks](../prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md)

The seven reserved groups include eight source files. The [receiver screen](ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md) found ten provisional windows, totaling 34.7 hours. Each group has one [timing-verified 20-minute slice](ESA_CONFIRMATION_TIMING_RESULT.md) with room to compare [two training lengths at the same development cadence](ESA_CONFIRMATION_CADENCE_RESULT.md). Confirmation fits will use separately frozen selection, prediction, and error rules. [Reservation and grouping](../PROVENANCE_VERIFICATION.md)

The reserved flights and development recording 187 share the same identified
iMAR inertial instrument. Calibration errors can therefore persist across
flights. [Instrument provenance](ESA_INSTRUMENT_PROVENANCE.md)

## Wuhan development lead

The inspected sample uses a NovAtel SPAN HG4930. Its IMR header gives the units and timing for recorded angular and velocity increments. A supplied trajectory combines GNSS and inertial navigation, so the independent receiver reconstruction would use the raw GNSS observations. This source remains a separate development lead. [Acquisition and instrument details](ACQUISITION_HISTORY.md)

[Earlier acquisition and format record](ACQUISITION_HISTORY.md) · [Current research plan](../ANALYSIS_ROADMAP.md) · [Study index](../STUDIES.md)
