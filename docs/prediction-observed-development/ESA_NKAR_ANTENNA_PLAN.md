# Replay the published antenna corrections on the two-minute comparison

Use development flight 187 on GPS week 2269. Keep the original aircraft
path, ground reference point, transmit times, raw ranges, satellite
support, final IGS orbit and clock products, and signed score weights.
Compare the two flight-era IGS20 antenna calibrations on the exact GPS L1
and L2 entries. Require one date-valid record per satellite and the exact
Nuuk Museum receiver antenna and radome type. Require adjacent 30-second
CODE attitudes in the IGS20 terrestrial frame for every satellite query.

Measure the effect of the satellite antenna phase-center offset and
pattern on both receivers, then add the ground antenna offset and pattern
at Nuuk Museum. Use GPS L1/L2 ionosphere-free coefficients and actual
transmit and receive geometry. Compute signed range changes before removing
the common receiver clock and applying the saved weights. Keep corrections
separate so readers can see what cancels in the comparison. The calculation
uses CODE attitude with the original IGS combined products as a sensitivity
test. It does not estimate receiver tracking bias, aircraft antenna response,
phase wind-up, or multipath. It does not refit the path or change the rank.

Use one task, one thread, the standard cooperative wall limit, one setup,
240 aircraft pair checks, and 120 ground pair checks. Read only the sealed
development evidence and public calibration inputs. Before launch, qualify
the time and frame conventions, azimuth interpolation, signed corrections,
signal combination, and failure checks. Use the checked technical recovery
policy. Report the projected changes and whether any independent aircraft
error cap was established. Zero new fits and zero reserved flight reads.
