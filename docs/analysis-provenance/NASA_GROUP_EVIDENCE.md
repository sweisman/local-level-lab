# NASA results by recording group

The [current evidence table](nasa-group-evidence-current.csv) has one row for each
of the 27 conservative groups containing the original 53 stretches. It brings
together the original fitted model preferences, the comparisons with the field
set to zero, the earlier prediction checks, the four-group matched forecast
audit, and the two paired-accelerometer comparisons.

All four groups in the matched forecast audit were already in the table. One
also appears in the earlier three-model pilot and three appear in earlier
single-model transfer checks. The four-group audit has 15 scorable forecasts
out of 16. In three groups both same-field shape comparisons favor globe and
the specified-field globe alone meets the fixed position limits on all three
GPS tracks. The other group favors globe at the specified field, misses the
position limits, and lacks a zero-field disc forecast. The two accelerometer
pairs overlap two of these four groups.

Each group keeps its earlier representative and the separate stretch chosen for
the later matched audit. Empty audit cells mean the group was outside that
study. The table keeps a recorded numerical stop distinct from a completed
forecast that misses the position limits. The GPS tracks and simultaneous
recorders contribute checks within a flight. These 27 groups supply development
evidence and zero independent confirmation groups.

Verify the source hashes, group memberships, forecast rankings and exact CSV
from the repository root. Substitute `write` to generate missing outputs. The
checker reads only saved evidence and makes no fits.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 --reserved-threads 0 -- ~/venv/bin/python -m lll.ilvis0_group_evidence_current check
```

[Source hashes and totals](nasa-group-evidence-current-receipt.json) ·
[Earlier prediction ledger](nasa-group-evidence.csv) ·
[Zero-field fitted costs](NASA_ZERO_FIELD_BY_GROUP.md) ·
[Matched forecast audit](../ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md)
