# Selective-precision derivative prototype

The archived long-record benchmark showed that replacing every wide derivative
with ordinary precision fails its unchanged tolerance. Its saved failures
involve ten of the 26/27 parameter columns. This prototype retains wide
derivatives for those ten original parameter indices: 2, 3, 4, 9, 11, 14,
16, 18, 19 and 20. The remaining seventeen use ordinary precision. The
physical-value path, motion equations, inputs and output ABI remain the
reference path.

1. Add a hash-bound C++ source transform in `analysis/lll/ilvis0_hybrid_tangent.py`.
   Keep the original wide source and frozen results untouched.
2. Test source mapping and all six candidate/processing cases on a generated
   two-second history, comparing bitwise values and every derivative against
   the reference tolerance.
3. The separate long-record gate uses the same six twenty-minute generated
   candidate/processing cases as the archived benchmark: 300 Hz increments,
   1,200 query epochs, all 26/27 derivative columns and one fixed nonzero
   parameter point. It allows six task identities, exactly two native tangent
   calls per identity and at most 5,184,000,000 packet/query work units.
   Reserve one worker and one numerical thread for at most two hours, with no
   retries. Record complete arrays, compiler/source/environment hashes,
   binary hashes and per-kernel CPU time. Require bitwise-identical coordinates
   and residuals and every derivative within the existing 2×10⁻¹⁰ absolute
   plus relative tolerance. A failure remains a failure; it does not change
   fitting or authorize any observed-data use.

This is software qualification, with no observed records, optimizer starts,
Earth-model decisions or use of protected confirmation groups. It cannot be
promoted into training or prediction without further qualification.
