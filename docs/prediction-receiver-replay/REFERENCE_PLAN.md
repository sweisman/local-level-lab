# Receiver-target reference replay

Build a reference distribution for how well a known generating model
predicts later noisy receiver positions. Use the 299 original calibration
seeds and the original 24 fit identities per seed. Open no validation cases
or aircraft records, including the seven reserved ESA groups.

Keep the three generating models, two instrument noise laws and two
simulated processing cases separate. For each of these twelve scenarios
and each seed, select one of the two starting points by its sealed
earlier training objective. Break ties by start number. Use no later
values in the choice. Replay the noisier receiver target for only that
primary, using the original receiver law and continued final training
coordinate transform. Verify the original receiver prefix by hashes.
For the seed already replayed, reuse its exact per-fit scores.

Save 299 seed tasks with 24 charged training-cost reads and 12 charged
primary checks each. Use one worker and one numerical thread with a
finite 30-minute wall allowance. Keep an unavailable seed in every
affected scenario and preserve any technical interruption. Support
task-level restart using the existing verified continuation policy.

Summarize noise-target and exact-position forecast error at the median
and 95th percentile for each scenario. Keep seed IDs so scenarios that
share the same random draws are never counted as independent flights.
These are own-model reference scores for the original simulator. They
leave actual aircraft errors, the matched three-candidate rule and
independent validation of the new score open.
[One-seed replay](RESULT.md) · [Decision rule](../PREDICTION_GROUP_DECISION.md)
