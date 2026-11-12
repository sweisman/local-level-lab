# Known-answer error-law identification trial

This finite software study asks whether earlier IMU and receiver errors can
distinguish three declared error laws and support later receiver predictions.
It uses synthetic linearized error histories only. It does not fit an aircraft,
inspect protected recordings, or calibrate an Earth-model decision.

Four independent tasks cover two generating laws (the reference law and a
receiver-persistent law) at one-second and ten-second sampling. Each task uses
exactly 100 predetermined seeds. Each history has 40 epochs: the first 30 may
select the error law and fit a constant receiver offset; the final 10 are
withheld until after selection. Candidate laws are the reference,
receiver-persistent, and gyro-bias alternatives. All candidates have the same
declared physical mean design. Law compatibility uses a development radius of
2 restricted negative-log-likelihood units. If compatible laws imply future
standard deviations differing by more than 1.25 times, or future means
differing by more than one smallest standard deviation, the rule abstains.
These cutoffs are exploratory, not calibrated confidence limits.

Each task first calculates training-only local covariance information for the
receiver-white, receiver-persistent and gyro-bias scales. For each seed it
records the earlier-only classification and separately scores oracle-law and
provisional-selected-law withheld coverage. The later values never select a
law. Report selection, abstention, rank, interval width and empirical coverage
separately; do not call a numerical minimum identified without supporting
evidence.

The study uses one worker and one numerical thread, a 900-second wall limit,
four tasks and 400 predetermined histories. Each task allows one local-rank
operation and 100 history classifications, charged before calculation. A
history classification is declared as four numerical steps: three candidate
law evaluations and one oracle prediction. Total finite limits are 404
operations and 1,624 steps. There are no native aircraft calls, optimizer
starts, original-file reads or confirmation reads. The source, input recipe,
software tests, numerical environment, result hashes and task-level recovery
qualification must be verified before launch. Interrupted starts stay charged;
sealed task results are reused.

The trial is diagnostic even if all tasks execute. Full nonlinear known-answer
prediction, physically adequate observed prediction and calibrated coverage
remain separate gates in [the uncertainty plan](../PREDICTION_ERROR_LAW_PLAN.md).
