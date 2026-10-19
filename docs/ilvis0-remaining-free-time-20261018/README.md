# Releasing the remaining time-alignment solutions

**Historical preparation, superseded before any native evaluation.** This version
was not run; the corrected [v2 study](../ilvis0-remaining-free-time-v2-20261018/README.md)
preserves the completed comparison. Counts and future-tense descriptions below
record the original preparation, rather than current project status.

This bounded test asks whether an unresolved stretch gives repeatable results
when its time alignment is fitted freely again. The preceding
[fixed-time profiles](../ilvis0-remaining-time-profile-20261018/RESULTS.md)
passed all ten checks: two controls and eight restricted fits. Both starts agreed
at every fixed offset under both processing assumptions.

The new test keeps the measurements, physical models, parameter bounds and
stopping requirements. It tests only the zero-field globe fit of stretch
`0e73879f98c3b701fd7c42df`; the other model fits are preserved for later review.
It does not change the published 50 globe / zero flat / three unresolved count.

Two fresh controls precede four free-time fits: a primary and a repeat under each
processing assumption. Each starts from its lower-cost verified profile endpoint,
then releases every original parameter, including timing. Choosing between two
endpoints does not demonstrate a global optimum.

[Finite implementation plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).

Runtime receipts and progress are recorded separately from this guide. Check with
`~/venv/bin/python analysis/status.py`.
