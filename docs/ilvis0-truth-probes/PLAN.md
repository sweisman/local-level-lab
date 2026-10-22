# Check ambiguity under the actual long-study observations

The earlier ray test used a zero-reference fixture. This separate diagnostic
uses the original long study’s sealed specified-field cases, nonzero truth
vector, five perturbed training observations and future time. It does not
change or resume that study.

There are four identities: zero/profiled upstream removal and north-negative/
north-positive objectives. Use the saved tangent Jacobians at the actual truth
for the five training times 2, 10, 30, 180 and 290 seconds, and at 438 seconds.
All 27 normalized physical columns remain. Propose a direction z in [-1,1]²⁷
with a one-thread, five-second LP; require linear training changes from 0.5 z
to be within ±1 metre. Check the represented primal witness exactly. This
is a proposal, not proof of nonlinear feasibility or an exact optimum.

For every direction evaluate all three fixed scales: 1/50, 1/20 and 1/10.
The normalized point is the original truth plus `0.5 * scale * z`. Reject an
out-of-box point; never clip it. Save all three points before their outcomes.
Each gets one full native batch at the original five training times and future
endpoint. Compare training predictions with the **stored perturbed observations**,
not the zero expansion or noiseless truth. The limit stays ±1 metre on all
15 coordinates. The later outcome cannot decide training feasibility.

| Resource | Per identity | Maximum total |
|---|---:|---:|
| Started identities | 1 | 4 |
| LP proposals / exact primal checks | 1 / 1 | 4 / 4 |
| Fixed candidate calibrations | 3 | 12 |
| Native batches / queried epochs | 3 / 18 | 12 / 72 |
| Conservatively charged packet visits | 1,728,000 | 6,912,000 |

Use one numerical thread, reserving two for the original long-record job,
and a ten-minute cooperative ceiling. Freeze all source, input references,
environment, compiler and counts before launch. No nonlinear optimizer
starts, aircraft reads, process signals, retries, outcome-selected scales or
allowance expansion.

Report every candidate and the later spread among actual training-compatible
calibrations plus the known truth. Preserve the original width targets of
20/20/50 metres. A sampled spread is not an outer uncertainty bound; a smaller
one would not prove uniqueness. This is generated numerical evidence, not a
native execution-error proof or an aircraft confidence claim.
