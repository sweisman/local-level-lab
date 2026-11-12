# Revised fast tangent: paired-fit development gate

## Question

The revised fast derivative passed all six saved-point checks. Does it also
produce the same fitted and withheld predictions as the established wide
derivative on the **three ESA development cases that failed the first paired
comparison**? A derivative check at a fixed point does not answer this after
an optimizer moves to a new point. In the old result, the wide fit passed in
two of these cases and failed in the third; the third cannot by itself qualify
the faster method.

## Fixed comparison

Use only development recording 187 and the prepared measurements from the
sealed 24-pair ESA study. Select the three failed case identities before
fitting: `flat_still-0-reported-short-v1-1`,
`flat_still-0-reported-persistent-v1-0` and
`flat_still-1-reported-short-v1-0`. Within each case, fit the wide and revised
fast derivatives from the same initial parameters under one frozen current
source, numerical environment, receiver error law and processing assumption.
Keep the original 800 training positions and 400 withheld positions, all
three coordinate axes, calibration bounds, optimizer and stopping checks.
Neither fit may read a withheld position before its forecast is saved.

The only within-pair method change is the tangent derivative implementation.
Reuse the common fitting and scoring library, not a copied worker tree. Bind
the wide, first fast and revised fast source hashes, prepared-input hashes and
the six-point improvement receipt. Do not read original telemetry or any of
the seven reserved ESA groups. Preserve the earlier 21/24 finding unchanged.

## Gates and allowance

First run source-bound software tests for exact input reuse, loader selection,
all nuisance columns, scoring isolation, charge accounting and an interrupted
task resume. The observed study then has **three paired tasks**. Each pair
has at most two fits of 200 evaluations and one forecast each: 402 charged
native calls and 77,621,507,200 packet/query visits per task. Across three
pairs the maxima are 1,206 calls and 232,864,521,600 visits. Use at most three
workers of one numerical thread each and a cooperative four-hour wall cap.
Freeze a finite continuation and verify reboot recovery before launch. Charge
before execution; never rerun a sealed result or enlarge a completed
allowance.
If interrupted, close the original only after its workers have stopped. A
separate continuation may charge at most four attempts per unfinished task,
nine technical interruptions total, a cooperative four-hour wall cap and a
5 GiB free-space floor. It must reuse the same source, inputs and environment;
completed failures are not eligible for continuation.

For the two cases with a qualified wide reference in the old study, require
the revised fast fit to qualify with the same numerical, physical-screen and
all-column classifications and at most **0.01 m maximum position difference**.
For the third case, report whether both new fits qualify. If either fails,
preserve the numerical failure and withhold a substitution decision for that
case; a tiny saved-point derivative difference cannot cure an unqualified
reference. A failed pair remains a failed method gate. Even three passing
pairs only clear the way for a separately frozen all-24 paired substitution
check; they do not qualify replacing the wide method or make an Earth-model
decision.

[Six-point result](../esa-observed-hybrid/same-point-v2/README.md) ·
[Original paired comparison](../esa-observed-hybrid/combined/README.md)
