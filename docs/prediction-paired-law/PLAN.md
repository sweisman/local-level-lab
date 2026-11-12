# Paired aircraft error-law pilot

**Status: preparation, not launched.** This is a finite development check of
training-only error-law comparison. It is a prerequisite to, not a replacement
for, the full independently seeded coverage study in
[the uncertainty plan](../PREDICTION_ERROR_LAW_PLAN.md).

## Question and cases

Can two fixed candidate IMU error laws be fitted to the **same** generated
aircraft measurements and compared using only the earlier receiver positions?
The previous 48-case integration matrix generated different measurements for
each law, so its scores cannot answer this question.

Preselect 12 generated recordings: three physical generating models × two
upstream processing cases × two generating IMU error laws. Every recording is
fitted twice, once under each fixed candidate law, for 24 total fits. Use one
declared initial point, seed 71, the interior calibration case, the 300 Hz
header-elapsed clock, two minutes of turning and climbing motion, 119 receiver
epochs, 79 earlier epochs and 40 withheld epochs. Keep the existing physical
bounds, all 26/27 nuisance columns and the established 10 m horizontal / 30 m
height RMS screen. Each candidate is fitted to its own generating physical
model; this pilot makes no Earth-model vote.

Save the measured IMU increments, timestamps and earlier receiver rows once
per recording. Both law fits must bind to those exact hashes. Save both fits,
their Gaussian training scores, forecasts and physical/future-receiver
conditional error diagnostics before generating later physical truth or later
receiver reports. Rank the complete training scores only when both fits pass
their numerical stopping checks. Record close scores, active calibration
bounds, distinct future uncertainty and every abstention. The numerical
minimum is not a calibrated law choice; no scientific decision is made.

## Work and release gate

Each of the 24 fits has at most 200 evaluations plus its declared forecast and
covariance construction. The derived per-recording ceiling is 239,816 native
calls and 1,506,051,012 packet-query visits across both candidate fits. Each
recording constructs 36,000 intervals and 36,199 samples. The two generating
law cases reserve exactly 649,206 and 433,212 normal variates, respectively,
including future receiver draws. These are conservative finite ceilings;
actual attempted work is recorded separately. Use four
single-thread workers and a cooperative two-hour ceiling. Source and numerical
environment hashes, task-level recovery qualification, immutable inputs,
charged starts and sealed failures are required before launch. A reboot may
resume unfinished tasks under their unchanged allowance; completed results
and failures cannot be retried.

The pilot succeeds as a **technical comparison** only if every task preserves
the same measured prefix across both fits and saves both candidate forecasts
before withheld data are opened. Numerical convergence, physical adequacy,
training-law score separation, active-bound frequency and empirical withheld
coverage are separate reported outcomes. Any failure is retained; it does
not trigger a relaxed gate or a rerun under the same identity. No observed
aircraft recording or protected ESA confirmation group is an input.
