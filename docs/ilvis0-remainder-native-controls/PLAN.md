# Conditional remainder: fixed native controls

This software study compares the existing integration bound with a separate
candidate that tightens only the initial force Taylor remainder. It uses
generated inputs, not aircraft observations. Existing studies remain unchanged.

There are twelve identities: three physical models, two processing assumptions,
and physical-domain versus synthetic force-constrained bounds. Each input is
the first 800 packets of the qualified eight-minute generated history, retained
bit for bit. Prediction is at 2.5 seconds. The original broad 27-parameter box,
±1-second clock, expansion, 24 shared error columns and normalization stay fixed.
The synthetic constraint limits initial force change to ±0.2 m/s² on each axis.
It is a software condition, not a measured aircraft error allowance.

Each identity reserves four native queries, two bounds and four fixed probes.
Both bounds are saved before off-center outcomes are evaluated. The known probes
are center, two corners and one mixed point for the physical domain; the
constrained scope uses fixed small calibration changes with full clock extremes.
Every probe must belong to its declared domain. No probe may be skipped or replaced.

Require unchanged shared maps, caps, bindings, physical bounds and native centers;
nonwidening remainder arrays; a strictly smaller force remainder; and containment
of every probe. The native center tolerance is 1 micrometre; the separate fixed
probe arithmetic allowance is 10 micrometres. These are software comparison
tolerances, not sensor accuracy or a whole-program rounding proof. Preserve
packet-boundary counters and validate them against actual clock/query geometry.

| Resource | Per identity | Total maximum |
|---|---:|---:|
| Native queries | 4 | 48 |
| Conservatively charged packet visits | 3,200 | 38,400 |
| Interval bounds | 2 | 24 |
| Logical bound steps | 14,400 | 172,800 |

Before each bound reserve complete 800-step source, derivative, point and direct
streams. Each constrained identity reserves six LP proposals and 24 exact
support checks. Each identity reserves one reference, one typed force proof,
two remainder-certificate calculations, four oracle checks and one matched
comparison. All auxiliary charges and artifacts are saved.

Use one worker with one numerical thread, reserving two for the current long
study. The cooperative limits are 180 seconds per bound and 4,800 seconds for
the study. No optimizer starts, aircraft reads, retries, process signals or
allowance increases. Freeze source, generated inputs, compiler and environment
before launch. Seal failures as well as successes. Publication reads saved
artifacts only.

Passing qualifies this short native component only. Useful complete-history
ranges, whole-period coverage and a defensible observation-error law remain
separate requirements before new withheld aircraft fits.
