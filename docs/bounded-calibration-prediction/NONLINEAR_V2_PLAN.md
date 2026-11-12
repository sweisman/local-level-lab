# Corrected nonlinear aircraft technical release

The first 24-case release is terminal. Its frozen adapter used package-relative
imports, which the study runner cannot resolve when it loads a source-frozen
file. All 24 identities recorded the same import failure before any native
call or generated observation. Those failures and their charged identities
remain preserved; no task in that release will be retried.

This second release keeps the scientific question, seed **271828**, 24-case
physical/processing/noise/calibration matrix, 120-second duration, 300 Hz
cadence, 119 receiver epochs, 200-evaluation fit ceiling, two withheld targets,
2.5% + 2.5% interval allowance, four single-thread workers and 7,200-second
cooperative ceiling. Its per-task ceiling remains 239,816 native calls and
1,506,051,012 packet visits. The adapter now uses absolute package imports.
A required test loads it through the same standalone file mechanism used by
the worker and checks that no relative imports remain anywhere in the file.

Qualify fresh source/environment hashes, the full required software suite and
task-level recovery before creating a new manifest. The release is a technical
nonlinear coverage check, not a 95% calibration sample or an observed-aircraft
result. Preserve all numerical and physical failures without loosening the
frozen acceptance limits. No recorded NASA/ESA or protected confirmation
observation may be read.

[Original plan](NONLINEAR_PLAN.md) · [Current software control](README.md).
