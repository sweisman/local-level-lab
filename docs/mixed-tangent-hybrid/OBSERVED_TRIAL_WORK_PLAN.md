# Count possible derivative savings in the sealed ESA fits

Use all 16 paired fits from the [closed ESA comparison](OBSERVED_DISPATCH_FRESH_RESULT.md).
Check the saved full-precision and selective-precision records for each
start. Match every fit to the published result and verify the original
manifest, fit counts and charged work. Keep the earlier numerical results
and their forecasts unchanged.

A solver can check whether a proposed step helps before calculating its
derivatives. The existing value-only alternative has reproduced complete
traces on separate generated and recorded inputs. This audit asks how much
work that alternative could save on the longer ESA paths.
[Previous exact recorded check](../ilvis0-measurement-contribution/MATCHED_TRIAL_OBSERVED_RESULT.md)

Count distinct evaluation IDs in each fit's proposal history. A cached
evaluation can appear in several proposals. An evaluation accepted at
least once still needs its derivative. Count an evaluation as avoidable only
if it appears in the proposal history and was never accepted. Keep initial
and fresh stopping evaluations in the full derivative count. Count one
value-only call per distinct proposal and report the number of full
derivative calls that would remain under an identical solver path.

For each fit and each method in aggregate, report the fraction of fitting
derivatives that could be removed. Also report the break-even ratio of
value-only cost to derivative cost under a simple equal-cost-per-call
calculation. Leave compilation, forecasts and other solver work outside
this ratio. It is a planning estimate. Actual timing and identical solver
behavior would need a separately qualified study on these inputs.

One saved-data task with one thread and a 120-second limit may read exactly
32 fit artifacts and their binding metadata. Charge each fit before reading
it. Run no refits, compiler, forecasts or native evaluations. Read no
original recording, later receiver position or reserved group.
