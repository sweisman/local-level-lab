# Complete optimizer matrix qualifies

**All 48 generated computational cases, all 24 paired-start comparisons and
all four original-input replays pass the combined audit.** It checks the 44
completed cases from the interrupted matrix and four separately completed
controls. All 241 shared execution sources and the numerical environment match.

The original interrupted study stays unqualified, with its four interrupted
starts and their charges preserved. The combined result uses each computational
case exactly once; it does not relabel interrupted work or select among competing
fitted answers. All three generating candidates, both input formats, both
processing settings and the same original starts are covered.

The matrix took 51.0 minutes; the separate four-case completion took 4.6 minutes.
Their pre-execution software qualifications passed 352 and 364 checks. The
saved-only assembler passes 16 additional checks, including deliberately missing
or duplicate cases, failed fits, bad pairings, changed sources and environments.
It independently re-audits both source publications without running a fit.

This completes the declared generated-data optimizer coverage. A fresh
calibration/validation design still needs disjoint cohorts and a separate finite
review. No uncertainty threshold, aircraft confidence level or new Earth-model
finding follows. The original 53 aircraft comparisons remain unchanged.

## Evidence and reproduction

[All 48 completed cases](results.csv) · [24 paired-start comparisons](pairs.csv) ·
[Preserved interruption records](interruptions.csv) · [Audit plan](PLAN.md).

The [interrupted matrix](../timing-feasible-matrix/INTERPRETATION.md) and
[completion controls](../timing-matrix-completion/INTERPRETATION.md) retain their
own frozen sources, inputs, outputs, journals and verified publication receipts.
The combined receipt binds the auditor, tests, qualification evidence, exact
constituent completion hashes and combined report. Shared source snapshots remain
in the constituent publications; they are not copied into another worker tree.

With the [documented frozen environment and source restoration](../REPRODUCIBILITY.md),
re-run the saved-only check from the repository root:

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -c 'from pathlib import Path; from lll.timing_matrix_assembly import inspect; r=inspect(Path.cwd()); print(r["qualified"], r["cases"], r["start_pairs"], r["original_input_replays"])'
```

Expected output is `True 48 24 4`. The auditor rejects changed source files or
environments; restore its recorded versions rather than substituting newer code.

[Next analyses](../NEXT_STEPS.md) · [Technical roadmap](../ANALYSIS_ROADMAP.md).
