# Receiver-window stability under stated motion errors

**Question.** How many of the already selected receiver windows would keep the
same support decision if each reported speed, course and vertical rate had a
bounded error? This is a sensitivity calculation, not an estimate of those
errors or an Earth-model test.

Use the 52 saved, strictly decoded primary-receiver position blocks and the
2,365 target times from the completed receiver-support inventory. Keep the
existing 5/10/15-second rule, timestamps, and all rejected windows. No IMU
increment, fused navigation answer, Earth-model fit or protected ESA recording
is an input.

For each candidate window, retain its exact time/completeness result and bound
the motion predicates under independently bounded per-epoch perturbations.
Speed and vertical-rate extrema can move by at most their stated error; their
spans can move by at most twice it. A course-span bound is valid only where
every adjacent course change stays safely away from the 180-degree unwrap
branch. Classify a candidate as certainly accepted, certainly rejected or
uncertain. The selected width is stable only when that candidate is certainly
accepted and all longer candidates are certainly rejected. Abstention is
stable only when every candidate is certainly rejected.

Report at least zero error, and separate hypothetical error envelopes for
0.05 and 0.10 m/s per speed/vertical-rate epoch and 0.05 degree per course
epoch. These are **assumed sensitivity ranges**, not measured receiver
accuracy. Cross-receiver agreement may inform interpretation but cannot bound
shared GPS errors. Do not convert counts into confidence or use them to change
the historical support policy.

Implementation: a pure bound helper with deterministic edge-case tests, then a
saved-only report with input/source hashes and one row per original target.
The report verifies its sealed source inventory and charges zero native model
calls. It does not reopen the 53 Earth-model fits.
