# Fixed six-target hybrid assessment

This separate freeze covers exactly the six unresolved stretches from the completed
nine-target assessment that have not been tested with the qualified hybrid solver.
Selection uses saved completion status, not favorable model costs or gyro values.

The finite allowance is **24 starts / 4,528 native sweeps**, with four total numerical
threads, no retries and no allowance expansion. Eleven failed primary model/case
identities are each fitted from their latest saved primary endpoint and repeated
from that same endpoint with the fixed inward 0.01 normalized perturbation. Every
primary and repeat permits 200 fitting calls plus two diagnostics. Twenty-five
passing companion primaries are reused with their original artifacts and hashes.
Two completed controls permit forty fitting calls plus two diagnostics each.

Some stretches contain multiple failed model/case identities. **Every newly fitted
primary must pass its own repeat check**; a later passing pair cannot overwrite an
earlier failure. Per-pair results and an all-pairs-per-stretch gate are preserved.
All six primaries, every required repeat and both fresh controls must pass before
any stretch changes disposition. A passing repeat never replaces a failed primary.

The source targets are `0e73879f98c3b701fd7c42df`, `370cec66878c4c1cf84b4ceb`,
`50f24131843071ae9312c082`, `b4e44ddc0f130ecd45674c78`,
`bb8061a43b4f14b6262ceda1` and `da346f70a6661ee42cecea19`.
The seventh unresolved stretch is excluded and has a separate saved-tangent audit.

The solver, physical models, two processing cases, original measurements, selected
intervals, clock, covariance, calibration bounds and final checks stay unchanged.
Known-answer software qualification and the completed matched trial are preserved;
partial success in that trial does not establish that every target will resolve.

Applying the prior per-identity runtimes to every new evaluation cap gives an
estimated ceiling of **28.8 hours**. Actual completion may be earlier; the binding
limits are starts and native evaluations. Freeze sources, inputs, environment and
the task list before launch. Preserve charged interruptions, exclusive locks,
start/sweep journals and atomic results. Completed work cannot resume, and unused
allowances do not transfer. Publication performs no fits or automatic rollout.
