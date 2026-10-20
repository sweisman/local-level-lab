# Parallel native-control execution

Future studies can divide independent control cases among **four workers with
one numerical thread each**. This uses the same four-thread total more
effectively than reserving four threads for a mostly serial Python calculation.
Active and completed studies retain their original allocations and sources.

The new implementation freezes task identities, source/input hashes, numerical
environment, task assignments and finite allowances. Each shard owns an
immutable charge ledger. Interrupted work remains charged; merging rejects
duplicates, changed artifacts, incorrect assignments and altered deadlines.
Locked file descriptors pass from coordinator to children before execution,
preserving ownership if the coordinator disconnects. No process is killed.

All [nineteen execution controls](qualification/README.md) pass, including
twelve real fixture-worker launches. The separate [native compatibility qualification](native-qualification/README.md)
passes all 24 generated cases: native arrays match bit for bit and complete bound
reports match exactly. This is qualified software execution infrastructure. It is not used for observed fits or new scientific conclusions.
The reusable status command recognizes surviving shard leases and retains the
full reservation when a coordinator is absent.

[Implementation and qualification plan](PLAN.md) ·
[Analysis roadmap](../ANALYSIS_ROADMAP.md) · [Status guide](../../analysis/STATUS.md).
