# One inertial instrument across the ESA flight groups

Development recording 187 and all eight files assigned to the seven reserved
flight groups carry the label **RQH01**. The Technical University of Denmark
identifies RQH01 as its iMAR iNAT-RQH-4001, serial iNAT-RQH-0001, and lists that
unit in the 2023 Green Quantum and AirQuantumGrav campaigns. The campaign report
describes one iMAR unit mounted to the aircraft floor. Together these records
support treating the archive as **one instrument flown on separate flights**.
[Archive file catalog](esa-live-imu-files.csv) · [DTU equipment record](https://doi.org/10.11583/DTU.25673604) ·
[Campaign report, sections 3.2–3.4 and 7.1.4](https://earth.esa.int/eogateway/documents/d/earth-online/airquantumgrav-final-report)

The seven reserved groups can test whether a method transfers across flights.
Their calibration can share persistent errors from the same unit and aircraft
installation. The campaign ran without the external temperature-stabilizing
housing, and DTU records an internal electronics upgrade after these flights.
Any error model used for confirmation needs to cover the 2023 configuration,
including errors shared across flights and changes within a flight. The
equipment record supplies no bound on those errors. [Flight-group decision rule](../FLIGHT_GROUP_DECISION.md) ·
[Development recording and temperature range](esa-sample-report.json)

The report says the installation team made rough physical measurements of
the distances between the roof antenna and the sensors before refining them
in the navigation fit. Table 4 gives the fitted offsets. The original
installation measurements, with their uncertainty if recorded, could provide
a separate check on the position of the antenna relative to the iMAR and
GIRAFE. Time-tagged platform orientation and the roof antenna's phase response
are separate evidence needs. [Antenna offset sensitivity](../prediction-observed-development/ESA_CARRIER_LEVER_SENSITIVITY_RESULT.md) ·
[Platform orientation](ESA_GIRAFE_187.md#aircraft-motion-and-platform-state-in-the-two-minute-check)

The public verifier matches the nine file labels to the frozen reservation and
checks the seven groups' saved receiver layouts. It reads metadata only.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_confirmation_evidence
```
