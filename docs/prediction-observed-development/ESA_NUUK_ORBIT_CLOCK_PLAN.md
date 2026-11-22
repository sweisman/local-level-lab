# Final satellite orbit and clock check

Use the 240 saved half-second carrier pairs from the open ESA development flight
and the previously constructed aircraft displacement that vanishes at the four
Nuuk ground anchors. Test whether the published IGS orbit and clock changes
supply the signed range pattern needed to hide that displacement.

Keep the original aircraft path, transmit times, atmospheric correction,
satellite matches, and receiver-clock removal. Evaluate the final SP3 orbit at
the same transmit time as the broadcast orbit. Compare signed range changes for
the orbit, clock and their sum on identical satellite support. Report centered
RMS, signed alignment, and carrier residuals for both fixed paths. Reproduce the
saved broadcast ranges before using the comparison. This isolates the effect of
the archived product substitution at fixed observation conventions. Effects such
as satellite antenna adjustments and errors shared by the products remain open.

One task uses one numerical thread and a 180-second cooperative cap. It charges
one setup and 240 pair checks of 99 bound steps each, with zero fits and zero
reads of reserved aircraft data. Qualified task-level recovery preserves the
original allowance and charges an interrupted replay separately.
