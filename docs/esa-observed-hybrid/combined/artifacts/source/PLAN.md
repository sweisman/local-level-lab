# Source-bound selective-tangent check on ESA development data

## Question

Can the selective-precision tangent replace the wide tangent in the
recording-187 development fitter without changing its training-only prediction
boundary, numerical decisions or later positions, when both use the same
current source and prepared measurements?

## Frozen comparison

Use the 24 case identities and exact prepared measurement bytes of the completed
ESA wide pilot:
one selected twenty-minute recording-187 interval, three physical candidates,
two processing settings, two working receiver-error policies and two declared
starts. Keep 800 earlier receiver positions for fitting and 400 later positions
for scoring. Preserve all measurements, starting values, optimizer, 200-evaluation
per-fit ceiling, physical bounds, gravity anchor, stopping checks, accuracy
screens and training-only primary selection. Run wide and selective fits for
each case under one newly frozen source and environment. The tangent loader is
the only within-pair difference. The old wide pilot is a historical result,
not the substitution reference: 14 files in its frozen source closure have
changed in the live tree, including the training-and-forecast function. Reusing
its 22 fitted outcomes as if they came from today's source would confound this
check. Read no original aircraft file or protected ESA confirmation group.

Require the published wide observed pilot and both completed generated
long-fit studies as source/input/environment-bound parents. Qualify a new
standalone adapter before preparing the study. Reuse the wide pilot's prepared
input bytes; hash and compare every copied input. Freeze new source and
environment hashes, the parent completion hashes and the unchanged source
protocol. Use four workers with one numerical thread each and a sixteen-hour
cooperative wall ceiling. Each of the two fits in a task permits at most 201
native calls and 38,810,753,600 packet/query visits; across 24 paired tasks
the ceilings are 9,648 calls and 1,862,916,172,800 visits. Charge before
execution. Do not retry a
completed or failed task, expand an active allowance or alter the existing
pilot's failures.

For each completed new pair, compare the two saved training costs, convergence,
all active columns, training-only input binding and every later
three-dimensional position. Report the historical 22 qualified wide starts
separately, without using them to decide whether the substitution works.
The largest position difference may be at most 0.01 m. The fixed training-cost
selector must choose the same primary start in the two new paths wherever both
starts qualify. Report all differences and every new failure. The two old
deadline failures remain unchanged. A complete substitution gate requires all
24 new pairs to finish and meet the fixed tolerance, with identical numerical
and physical-adequacy classifications.
This is a software-method check on a development recording, not an independent
Earth-model replication or calibrated detection.

## Sequence

1. Build a small paired observed evaluator that calls the existing shared fitting
   and scoring components with explicit tangent loaders. Do not copy an
   entire historical worker tree or patch a process-wide module.
2. Test exact input reuse, source and environment binding, complete nuisance
   columns, later-position isolation, charge limits and frozen-file direct
   loading. Run the source-bound qualification before study preparation.
3. Run the finite 24-pair study, independently replay all saved results and
   matched comparisons, then publish every outcome and update the roadmap.
