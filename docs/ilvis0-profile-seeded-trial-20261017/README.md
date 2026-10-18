# Release time after searching the timing profile

The completed profile found that fitting cost rises and falls as time alignment
changes. A local solver can stop at different fitting solutions. This trial
searches the five verified timing seeds, then releases time under its original
bounds and applies the unchanged full stopping checks.

The two repetitions use profile fits from their own original nuisance starts.
All five points are retained. Both fresh controls, both full fits and prediction
repeatability must pass. This is solver development on an existing recording,
not a new independent observation or a proof of a global optimum.

The frozen ceiling is four identities, two optimizer starts and 174 native calls,
with four numerical threads and no retries. The trial publishes automatically;
a separate saved-companion review is required before changing current findings.

All 24 software-qualification checks passed, including known multiple-minimum
examples, restoration of free time and real-ledger failure accounting.

The observed trial stopped after 53 charged calls. Both controls passed; the
completed target failed time stationarity, and the repeat was interrupted during
an accounting write. The incomplete transaction is preserved and blocks resume.
The [saved-result audit](../ilvis0-profile-seeded-audit-20261017/README.md) locates
the completed target about 1.2 nanoseconds from an integration-packet boundary.
It directs the next check to both sides of that boundary, under a separate freeze.

[Finite plan](PLAN.md) · [Timing profile](../ilvis0-interior-timing-profile-20261017/RESULTS.md) ·
[Current findings](../CURRENT_STATUS.md).
