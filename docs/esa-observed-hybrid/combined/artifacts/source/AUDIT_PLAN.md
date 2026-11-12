# Independent audit of the paired ESA tangent check

The original study closed terminally after an interruption. The audit must
read its sealed outcomes together with the separately frozen continuation
stages and the published wide-pilot parent. It does not fit a model, read an
original aircraft recording, or inspect a reserved ESA confirmation flight.

## Evidence to verify

1. Match the 24 case identities, model choices, starts, limits and numerical
   environment to the original and continuation manifests. Verify every
   source, input, charge and result hash. Reuse the 14 original completed
   outcomes; retain the four original technical interruptions and any later
   interruptions as charged attempts. No identity may have two completed
   outcomes. The qualified source list is a subset of each execution manifest:
   accept only its explicit frozen engine extension.
2. Compare the copied receiver observations, IMU increments, selection,
   training split and working-error inputs byte for byte with the completed
   wide pilot. The older pilot's fitted outcomes are historical because its
   source differs; they are not the paired substitution reference.
3. For each new wide and selective fit, check every active nuisance column,
   the earlier-only receiver prefix, saved forecast boundary, compilation
   provenance, numerical charges, and independently recomputed receiver errors
   and physical-adequacy labels.
4. Compare each same-source pair in metres. A qualified substitution needs all
   24 cases returned, equal numerical and adequacy classifications, no missing
   nuisance directions, a maximum three-dimensional forecast difference of
   0.01 m, and the same training-cost-selected primary start wherever both
   starts qualify. Preserve every failed or incomplete case.

Report cost differences, prediction differences and failures even if the gate
does not pass. If the frozen deadline or technical-attempt limit leaves identities
unfinished, publish a verified 24-row table with those identities marked missing
and the substitution failed. Never turn a missing fit into a passing pair or
retry a sealed outcome. A passed software substitution is not an Earth-model detection,
a receiver-error calibration, or an independent ESA replication.

The checker source and its own passing test report will be hashed with the
published audit result. The original and continuation sources, inputs,
allowances and outcomes are never edited by the audit.

The original metadata check verified all 134 qualified source files and the
19 explicitly permitted runtime files. Six focused single-study audit tests
passed. A new read-only combined-task ledger now checks the parent and every
recovery stage, including completed failures and technical charges; its three
focused tests pass, including deadline and attempt-cap failures. A combined-study view now routes each identity and its
saved artifacts to the correct sealed stage. It shares one checked archive
catalog across stages; its metadata test passes. The physical replay and
publication must use that view after the continuation closes. Seven focused
publication tests verify that an open or unverified report is rejected,
while a terminal missing pair is retained as a failed gate,
that the bundle contains the 24-case table, every charged attempt and hashed
auditor sources, and that a changed artifact fails receipt verification. The
bundle also requires the exact 17 named audit tests to pass; an unrelated
passing XML report is rejected. The gate accepted an actual pytest report.
The final publication must preserve the verified
report, its own source, this audit plan and the frozen execution plan in a
hashed receipt. Its verifier
checks that the receipt agrees with the report and that archived source bytes
match the published source hashes. These software
tests do not establish that the observed paired study qualifies.

The combined preflight suite now passes all 17 focused tests, including the
report check for a measured forecast discrepancy and its fixed limit. Its fresh
XML report passes the publication gate. This verifies the auditor's software
controls before the recovery stage closes; it does not substitute for replaying
the closed 24-case result.

After the continuation closes, run the focused audit suite and seal the result
from a fresh process. The publication command replays the saved measurements;
it does not refit or read an original aircraft file. Run the replay only after
its four reserved worker threads are released.

```bash
PYTHONPATH=analysis /home/sweisman/venv/bin/python -m pytest -q analysis/tests/test_airquantumgrav_observed_hybrid_audit_v2.py analysis/tests/test_combined_task_evidence.py analysis/tests/test_esa_combined_publication.py --junitxml=docs/esa-observed-hybrid/combined-audit-tests.xml
PYTHONPATH=analysis /home/sweisman/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 --reserved-threads 0 -- /home/sweisman/venv/bin/python -m lll.airquantumgrav_observed_hybrid_combined_audit publish --project . --test-report docs/esa-observed-hybrid/combined-audit-tests.xml
PYTHONPATH=analysis /home/sweisman/venv/bin/python -m lll.airquantumgrav_observed_hybrid_combined_audit verify --project .
```
