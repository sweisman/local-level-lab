# Independent generated coverage check for the fixed changing-drift law

## Purpose and limit

Test the already fixed 15-state law from the
[fresh-seed pilot](../integrated-drift-v2-pilot/RESULT.md) on a new generated
cohort. This is a simulator-specific coverage check. It cannot calibrate
real-aircraft uncertainty, settle Earth-model comparisons or consume any of
the seven reserved ESA flight groups. Keep the pilot results and its law
unchanged regardless of the outcome.

## Frozen cases and budget

Use exactly 256 new seeds `2026111800` through `2026112055`. Even seeds have
physical vibration and odd seeds do not: 128 independent generated histories
per stratum. Each history lasts 120 seconds at 100 IMU samples per second;
receiver reports occur at seconds 0–120. The forecast conditions only on
reports 0–60 and scores 61–120 after it is saved. Keep every generator
amplitude, fixed law scale, initial true state, code version and numerical
environment from the sealed 16-case pilot. No fit, native call, aircraft
original or protected flight group is allowed.

Use one numerical worker and one thread, a 40-minute original wall allowance,
one original start per task, and at most 12,000 generated IMU packets plus
121 receiver reports per task. Qualify and freeze unfinished-task recovery
before launch. Preserve completed errors; never rerun them to improve the
result. A reboot may continue only unfinished tasks with unchanged scientific
inputs and separately charged finite recovery limits.

## Predeclared gate

For each whole history, failure means either a technical task failure or at
least one of its 180 later standardized coordinates exceeds the existing
`3.6351881983520586` conservative simultaneous 95% threshold. Count
histories once. Require all 256 technical tasks to complete and no more than
**one** simultaneous-range exceedance in **each** 128-history stratum.
With at most one exceedance, the exact one-sided 97.5% binomial upper bound
on that stratum's failure probability is about 4.28%; two Bonferroni-adjusted
strata give at least 95% joint confidence **under independent generated
histories from this specified simulator**. More failures, incomplete work,
or a changed law fails this generated gate. Do not loosen the rule afterward.

If the gate passes, the next step remains a separately frozen observed
development-recording adequacy test. These generated histories cannot
establish transfer to an actual aircraft, parameter uncertainty or a
scientific detection.
