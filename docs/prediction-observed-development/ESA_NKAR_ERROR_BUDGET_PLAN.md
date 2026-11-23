# Update the development flight’s carrier error budget

Use only the six pinned reports from development flight 187. Rebuild the
projection of the saved model-score weights onto the actual 120 one-second
Nuuk Museum intervals. Check it against the sealed projection and compute
separate sensitivity coefficients for the covered and uncovered directions.
Use the original aircraft ranges without a ground correction. The ground
correction learned on earlier data did not materially change those ranges.

Keep the prior illustration of a one-metre anchor error per coordinate,
two millimetres RMS in uncovered carrier directions, and the constructed
acceleration cap from the original score study. Use the exact geometric
remainder calculation at those caps. Calculate the largest covered-direction
RMS error allowed by the score gap. Compare that limit with the same budget
at Qaqortoq’s coverage. These caps are illustrative. Require separate evidence
for the actual aircraft caps before a decision.

Perform one deterministic verification on 240 saved half-second intervals
with at most 2,496 stored values. Use one numerical thread. No fits, original
measurement processing, or reserved flight reads are authorized. Preserve the
original budget. The revised receipt must reproduce byte for byte from the
pinned reports and record the missing caps explicitly.
