# What the compiled comparison establishes

**All six generated cases pass.** The calculation took 57.44 seconds, using six
native queries and 162 interval calculations covering 10,368 packet steps.
Each calculation retains all 64 packets. Every native position and corresponding
first derivative lies inside its computed interval; the maximum outside gap is
zero across all 27 parameters and both processing assumptions.

This qualifies the short compiled adapter connection. Its source, inputs,
environment, charges and outputs are sealed, and the saved publication passes
verification. No aircraft originals or optimizer starts were used. The slower
rational-reference controls and known-answer controls independently check
higher derivatives; the native reference supplies only first derivatives.

These results do not establish useful full-record uncertainty, all clock and
rotation boundaries, native execution error or an aircraft measurement-error
law. The long-record study and its width targets remain unchanged.

The nested state reports inherit the reference serializer's `dyadic_bits: 96`
label. That label does not describe the compiled endpoint encoding. Use the
saved exact endpoints and compiled-kernel metadata: this backend uses outward
binary64 intervals. This metadata issue does not change the comparisons and
must be corrected in a separate successor, preserving this freeze.

[Verified results](README.md) · [Frozen limits](PLAN.md) ·
[Packet adapter](../ilvis0-compiled-path-packets/README.md)
