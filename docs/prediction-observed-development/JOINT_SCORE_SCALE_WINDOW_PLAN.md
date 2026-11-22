# How much could a shared error scale change the decision?

Use the four sealed development settings from ESA recording 187 and the
existing [joint-score rule](JOINT_SCORE_ABSTENTION_PLAN.md). Divide every
score by the same positive variance multiplier. Keep the original physical
accuracy screen, four covariance assumptions, model hierarchy and
incomplete cases. Find the exact multiplier intervals where the rule would
give each result. Then intersect the two complete settings to see where
they agree. Reproduce the original dispositions at a multiplier of one.

The intervals describe sensitivity. They do not estimate the real variance
or provide a scale to use for the same flight. A change common to all
covariance assumptions cannot test changes in correlation or an error scale
that shifts after the training cut. The post-fit diagnostic also does not
propagate the effect a new variance law could have on fitted parameters.

The replay freezes its source, input hashes and environment. The limit is
four settings, two complete and two incomplete, with one thread, no fit
starts, no native calls and no new aircraft data.
