# One-packet native adapter qualification

Compare the new third-order interval packet adapter with the unchanged native
tangent kernel. Use the first packet, bit for bit, from each of the six qualified
generated histories: three physical models and two processing assumptions.
Preserve each initial configuration, calibration scales and processing convention.
Use the zero expansion point and query halfway through the first packet.

Each identity makes one native query, saving its position and all 27 derivative
columns. Then make one interval calculation per normalized parameter direction,
with path value zero and unit first derivative. The other path derivatives are
zero. Preserve every column, including clock and removal; do not select a subset.
This checks derivatives on a stable packet branch, not uncertainty over the full
physical parameter box or ±1-second clock range.

For every direction, compare native position and the matching first derivative
with the interval endpoints. Convert coordinate differences to metres with the
fixed per-case local scale. Any gap outside the interval must be at most one
micrometre for both values and first derivatives. These tolerances compare
software; they are not a sensor accuracy claim or a whole-program rounding proof.
Higher derivatives retain their independent known-answer component checks;
the first-order native oracle does not independently verify them.

| Resource | Per case | Total maximum |
|---|---:|---:|
| Started identities | 1 | 6 |
| Native queries / packet visits | 1 / 1 | 6 / 6 |
| Interval calculations / packet steps | 27 / 27 | 162 / 162 |
| Position / first-derivative comparisons | 81 / 81 | 486 / 486 |

One worker uses one numerical thread, reserving two for the running long-record
study. The cooperative ceiling is 30 seconds per interval calculation and
20 minutes overall. Freeze source, input, compiler and environment before launch.
Charge work before execution and preserve all failures. No retries, observed
fits, original aircraft reads, process signals or allowance increases.

Publication reads sealed results only. Passing qualifies this short adapter
connection; it does not qualify useful full-history bounds, complete clock or
rotation-branch coverage, native numerical execution or an aircraft error law.
