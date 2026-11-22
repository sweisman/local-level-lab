# Three-model generated preflight

The short software preflight completed one generated recording and three
candidate fits. It verified that all three candidates received the same IMU
increments and earlier receiver positions. Their forecasts and both kinds of
range were saved before later receiver data were generated. Its charged work
closed exactly, and the recovery checks passed.

The preflight allowed only eight fit evaluations per candidate. None converged.
All three receiver ranges covered the withheld path, so this case could not
distinguish globe from flat or a specified background field from zero. It is
one technical check, not a scientific result.
Their mean full horizontal widths were about 375–398 m, and every pair of
ranges overlapped at every withheld epoch. The
[saved range audit](matched-candidates-preflight-range-audit.json) records
those widths and overlaps without new fitting.

The [finite twelve-recording plan](MATCHED_CANDIDATE_GENERATED_PLAN.md) now
tests the same procedure with full fit allowances across three generating
models, two latitudes and two synthetic IMU error laws. The
[verified preflight report](matched-candidates-preflight-result.json) records
the completion and artifact hashes.
