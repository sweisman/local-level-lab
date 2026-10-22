# Compiled aircraft-motion calculation

The compiled midpoint step passes ten software checks. They cover all three
physical candidates, both processing assumptions, and derivatives through third
order against the separate high-precision rational calculation. A known-answer
acceleration/gain example checks the signs and higher derivatives independently.

This is a building block for faster uncertainty calculations. It preserves both
local motion solves and the revised coordinate update used by the native model.
Unsupported domains fail, including a rotation interval crossing the formula
switch. Source, compiler and binary hashes are recorded when the backend loads.

These checks do not establish full-record prediction ranges, complete timing
coverage, execution-error bounds for the native solver or an aircraft error law.
The packet-loop connection is the next separate check.

[Arithmetic](../ilvis0-path-arithmetic/README.md) ·
[Exact reference](../ilvis0-path-motion/README.md) ·
[Remaining prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)
