# Which recordings can support the main result?

The project preserves uploaded recordings so others can inspect them. Publishing a recording
and accepting it as scientific evidence are separate decisions. A recording can be useful for
exploration even when it cannot support the main result.

## Check the instrument and its history

A reviewer must establish which physical instrument produced the recording. Names or identifiers
supplied in an upload are not proof by themselves. The instrument must have completed the
[bench tests](BENCH.md) with the relevant settings before the flight.

Review binds approval to the exact original recording and the instrument evidence. Later testing
cannot qualify an earlier flight retroactively. Duplicate registrations of the same instrument
must be prevented, because repeated use does not create new independent instruments.

## Check the flight

The current main-result rules require both calibrations, enough steady cruise, sufficient
retained heading variation and acceptable recording integrity. Missing samples, uncertain
IMU orientation, incorrect settings or a failed numerical fit can exclude a flight.

The analysis must also be able to distinguish the required model predictions after allowing
for IMU and aircraft effects. A flight can pass the recording checks yet contain too little
separating information. Results that depend strongly on uncertain assumptions or data exclusions
need further investigation rather than stronger claims.

The stricter experimental analysis remains under development. Its implementation is shared
across research and analysis, but it has not been promoted to a validated final decision policy.
All currently reported scientific confidence remains provisional.

## Flight details and missing GPS

Airline, number, date and route help identify a flight, but selecting them in the app does not
verify that it flew. A dated public track can support review and check phone GPS. It must remain
a separate source with its own provenance and terms. It cannot currently bypass the missing-GPS
rules for the main result.

## Corrections and public records

Original recordings remain unchanged when software improves. Generated reports can be replaced
by running the new analysis, with their software version and evidence history retained. Approval
can be withdrawn if problems are found. Public reports must then reflect that withdrawal.

The project has no real instrument validation or independently validated final decision thresholds
yet. See [Validation](VALIDATION.md) for the current boundary. The [curation guide](CURATION.md)
preserves the exact approval commands, technical requirements and server operation details.
