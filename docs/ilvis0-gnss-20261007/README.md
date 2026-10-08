# Initial satellite-decoder audit, preserved history

The first six-file receiver-observation audit completed with 19,699 decoded epochs,
603,603 signal measurements and 326 GPS ephemeris packets. Original hashes, frame counts
and complete survey-record sequences passed. No original was deleted and no position
or Earth-model fit ran.

Its RT17 `code_smoothed` field incorrectly labeled a flag for filtered pseudorange
corrections. Both recorded flags were clear, but that cannot establish unsmoothed code.
The first sky-angle summary also lacked per-outlier provenance. Original exports,
reports and source snapshots remain in `data/ilvis0-gnss-20261007/`; this completed run
is frozen and must not be resumed with changed code.

The separately frozen [v2 audit](../ilvis0-gnss-v2-20261007/README.md) corrects the flag
semantics, preserves explicit RT17 smoothing uncertainty and records all angle outliers.
Use its implementation and reports for current status.
