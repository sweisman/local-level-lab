# Preserve original receiver line numbers across training splits

The [first frozen check](esa-matched-split-freeze.json) verified the original
receiver file on both passes. Comparing the nested training rows failed
before any weight calculation. The general receiver parser counts lines in
the stream it receives. Earlier versions passed it a subset and recorded
those subset line numbers as if they were original file positions.

The correction keeps each selected row's original line number while
passing the same subset to the shared parser. A known-answer test checks
that a report retains its original line number when it falls in two
different training splits. The source indices, observation values,
prediction times and requirement to exclude later coordinates are unchanged.

A separate v2 freeze allows the same two receiver passes and four weight
constructions on development flight 187 with zero fits and zero inertial
reads. The first check's two completed passes and failure stay recorded.
[Original failure and source paths](esa-matched-split-v1-failure.json) ·
[Input scope and commands](ESA_MATCHED_SPLIT_PLAN.md).
