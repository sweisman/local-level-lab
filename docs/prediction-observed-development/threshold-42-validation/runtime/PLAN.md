# Fresh generated check of a wider prediction range

## Question

Does the existing fixed 15-state changing-drift law contain at least 95% of
whole generated forecast histories when its simultaneous standardized-error
threshold is 4.2? This threshold was chosen after seeing the failed 256-case
development result, whose largest score was 4.115341. The old result stays
failed. Only a new, independent cohort may qualify this new threshold.

## Frozen input and finite work

- Keep the generated aircraft, sensor/receiver errors, propagation, earlier
  conditioning and covariance operator unchanged.
- Use 256 fresh seeds, `2026112400` through `2026112655`; even seeds enable
  the generator's physical vibration and odd seeds disable it. The two strata
  have 128 whole histories each. No seed from an earlier pilot or validation
  may be reused.
- Each history has 120 seconds at 100 IMU samples/s, 121 receiver reports,
  training through second 60 and 60 withheld seconds. Save the forecast before
  scoring withheld truth. A technical failure counts against coverage.
- One numerical worker and one thread; at most 12,000 generated IMU packets
  and 121 receiver reports per task, one original start and no native call.
  The original wall allowance is 2,400 seconds. Unfinished-task recovery must
  be qualified and frozen before launch. Completed passes and failures never
  restart; a reboot resumes only unfinished work with separately charged,
  finite recovery limits and unchanged source, inputs and environment.
- Do not read an aircraft original, reserved ESA group, or Earth-model fit.

## Gate

Fail a whole history if any of its 180 later standardized coordinates exceeds
4.2 in absolute value, or if the technical task fails. Require all 256 tasks
to finish and at most one failure per 128-history stratum. This gives an exact
one-sided 97.5% upper binomial failure bound of about 4.28% per stratum; the
two-stratum Bonferroni statement then gives at least 95% joint confidence
that each stratum's failure probability is below 5%, **for independent
histories from this specified generator**. Do not change the threshold,
allowance, seed set or gate after launch.

If it passes, only generated-software coverage has qualified. Aircraft error
coverage, model contrast and a scientific decision remain separate gates.
