# Check recorded aircraft motion with GPS carrier phase

The raw GPS measurements preserved for the [two-recording pilot](GPS_RECONSTRUCTION_PILOT_RESULT.md)
contain at least five usable-looking L1 carrier-phase readings at every
selected second. This covers 669 IMU8 epochs and 443 IMU21 epochs. Neither
recording has five finite nonzero L1 Doppler values at any selected epoch.
The phase counts screen the recorded health, lock, slip and half-cycle flags
at each epoch. Continuity between epochs and satellite geometry still need to
be checked.

Use the same two flight groups, second tags and common accelerometer windows.
First, qualify the sign, wavelength, satellite-clock correction and the
receiver-clock term against known displacements. Correct both endpoints for
each satellite using a single healthy broadcast ephemeris across the pair.
Require common L1 tracking, matching slip counters, supported time gaps and
full-rank geometry. Verify the calculation against independently generated
displacements with satellite motion, a free receiver-clock change and
constant phase offsets.
Keep unsupported intervals in the inventory without filling gaps. [NASA GPS
measurement model](https://ntrs.nasa.gov/api/citations/20250006484/downloads/GEONSMSR3_1.pdf) ·
[Broadcast ephemeris continuity study](https://doi.org/10.1007/s10291-014-0425-1).

Estimate displacement and a receiver-clock change from each supported pair,
without using inertial measurements or later onboard positions as residual
constraints. Compare the phase-derived motion with the code-derived and
onboard motion over the original windows. Keep training and later epochs,
temporal correlations and the geometry of shared satellite observations
separate in the report. Use the differences to assess the receiver contribution
to force uncertainty. The streams share satellite and propagation errors,
so the comparison alone leaves common errors and absolute coverage open.

## Frozen two-recording receiver pilot

Use the first 60 adjacent pairs from each original recording to check which
RT27 phase sign agrees with code changes across the same satellites. Remove
each pair's median range change from the residuals. Require at least 20
usable pairs, a median residual RMS at most 5 m and at least a tenfold
separation between signs. These code comparisons qualify the sign convention
and enter no displacement residual. Report the sign score for each
recording. [Trimble RT27 field reference](https://receiverhelp.trimble.com/oem-gnss/icd-subtype6-realtime-gnss-survey-data-27.html).

For all 1,110 original adjacent pairs use gaps of 0.75–1.25 s, at least five
continuous signals above 5° at both times and a design condition number
at most 100. Use one broadcast ephemeris within two hours of each pair
endpoint, with a deterministic tie break. Use the earlier L1 code position
as the spatial anchor and the code ranges for light time. Hold atmosphere
corrections at the anchor for both endpoints and record this approximation.
Solve the endpoint displacement and one common clock increment jointly.
Preserve unsupported intervals without interpolation or residual screening.

Cap the study at one displacement solve per pair and eight iterations per
solve, with zero inertial fits. Use two single-thread workers and a
cooperative three-minute limit. The workers save the charged pair inventory
before each block. Compare the earlier code and later receiver outputs only
after solving the phase displacement.
