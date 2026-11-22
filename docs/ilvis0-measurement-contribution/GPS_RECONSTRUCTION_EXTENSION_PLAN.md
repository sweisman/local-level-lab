# Reconstruct GPS positions on two additional NASA flight groups

Use the two remaining groups from the [metadata-only selection](MATCHED_PILOT_CANDIDATES_RESULT.md).
They are the 9.75-minute southbound IMU8 stretch and the 8.95-minute southbound
IMU21 stretch. Keep the original two pilot groups separate. Use the recorded
raw GPS ranges and broadcast orbit data, without inertial measurements or fit
results. This extends the receiver processing check to four distinct flight
groups. All four are southern and the receiver methods can share errors.

Bind each recording's source hash and group to the completed [GPS input
check](GPS_RECONSTRUCTION_PREFLIGHT_RESULT.md). Retain the first measured
millisecond tag in each GPS second in the saved interval, with no interpolation
or trimming based on solve outcomes. The two methods must have the required
input support at every retained tag. Use the original pilot's position solver,
one start and at most 12 iterations per method per tag. Use the initial onboard
position once as the starting guess; later onboard positions are used to
compare the independent calculations. Report convergence and signed
north/east/height differences, including 10-, 20- and 30-second acceleration
differences on intact intervals. Preserve missing or failed solves.

The selection pass verifies hashes and writes the exact tags without any
position solves. The reconstruction has two single-thread workers, a
five-minute wall limit, and at most 750 tags per recording. The exact
allowance is twice the saved tag count, with no IMU fits. Before launch bind
the solver inputs and environment and qualify task-level recovery. An
interruption can recover only unfinished blocks under a separately charged
allowance of one technical restart per block, at most two interruptions
and ten minutes for the recovery stage.
