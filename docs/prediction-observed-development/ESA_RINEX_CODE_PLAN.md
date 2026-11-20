# Rebuild receiver positions from ESA GPS code measurements

Use the sealed AIR1 excerpt from development recording 187 and the matching
IGS broadcast navigation file. Decode the RINEX 3.04 GPS observation and
navigation records and pass them to the existing broadcast GPS solver.
Verify the fixed-width field mapping with a known-value fixture. The only
starting position comes from the RINEX observation header and is used for
iteration. Every epoch starts from that same point.

Process all 1,041 half-second epochs exactly once under each of two fixed
methods. The first uses C1C code with the broadcast GPS ionosphere
coefficients. The second uses the C1C and C2W ionosphere-free combination,
using C2X only when C2W is absent. Both use the existing 5° elevation mask,
standard-atmosphere correction, equal range weights, and at most 12
iterations per epoch. No residual-based exclusions or retries. Report
the use of each L2 code, fitted range residuals, missing epochs and
the between-method position differences. RINEX epoch clock offsets
are retained. They are separate from the receiver clock fitted to code.

Before the run, hash the input bytes and executable source and record
the numerical environment. Use one numerical thread. Save the results
and hashes before inspecting any comparison receiver positions.
The seven reserved ESA groups remain sealed. This study reconstructs
positions from the same antenna used in the earlier export. A later
comparison can measure processing differences. Absolute airborne
accuracy and the adequacy of the prediction error law remain separate
questions.

[RINEX 3.04 format, Appendix A](https://files.igs.org/pub/data/format/rinex304.pdf)
· [Input provenance](ESA_RINEX_WINDOW_RESULT.md)
