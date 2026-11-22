# Reconstruct the two-minute motion from continuous carrier phase

Use the exact 240 half-second pairs from RINEX indices 799 through 1039.
They follow the last earlier position in the 400/120 comparison and
come after the gap recorded in the continuity preflight. Start from
the archived earlier receiver position. Never reanchor to a later
position. Retain the original observation time assignments and both
carrier channels at each accepted pair.

For each GPS satellite, difference the carrier phases in metres and
form the combination that cancels first-order ionospheric delay.
Compute the satellite positions and clock change using the same
healthy broadcast ephemeris at both endpoints. Evaluate the standard
troposphere model at the first position and at a preliminary end
position. Fit three displacement components and one free common
receiver clock change. Require the existing phase solver's geometry
and stopping checks in both iterations of the atmosphere correction.
Stop the continuous path at the first failed pair and retain its reason.

The study allows 240 paired steps, up to two displacement solves with
eight iterations each per step, one worker and one thread. The separate
score compares the resulting 120 matched positions with the export and
tests their effect on the archived same-field shape score, with earlier
receiver positions held fixed. Neither step performs inertial fits or
reads reserved groups. The result measures relative motion using the
same receiver antenna and one earlier position anchor.
