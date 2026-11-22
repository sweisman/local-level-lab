# Observed dispatch: technical correction

The first prepared observed dispatch study closed with **16 technical
failures and zero native calls**. Its adapter looked for the recovery receipt
under the study directory rather than in its sealed input bundle. The failure
records and charges remain in
`data/esa-observed-model-dispatch-globe-pairs`; no fit or physical-model
comparison ran.

The corrected adapter reads both recovery receipts from the study's sealed
inputs and verifies their hashes against a sealed parent proof. A regression
test gives the evaluator a study root that does not contain the live request
file, reproducing the first error before the correction. The fixed study has
a new identity, `data/esa-observed-model-dispatch-globe-pairs-v2`, and must
pass fresh source-bound qualification before preparation. It retains the
original sixteen cases, work limits, 30-hour wall ceiling, scientific inputs,
method choice and acceptance criteria. The first study is never restarted.

The recovery instructions in the original plan apply to the new identity
with the same finite continuation limits. This correction does not establish
an observed substitution result or alter any saved numerical preference.
