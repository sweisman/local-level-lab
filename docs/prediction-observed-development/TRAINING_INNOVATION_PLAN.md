# Check the ESA training error law without later positions

## Question

Do the two declared fixed error laws leave persistent patterns even in the
first 600 receiver reports used to fit the ESA development recording? The
600/400 forecast later misses its stated height ranges. This calculation
looks only at the earlier residuals, so it cannot be tuned to that miss.

## Fixed inputs and calculation

Use the two sealed 600-report fits, their saved training differences, and
their original receiver reports and IMU increments through the training
boundary. Reconstruct each law's **training** covariance operator from the
same source, model, clock, bounds and fitting inputs. Before describing
innovations, require the reconstructed operator to reproduce the saved
training cost and covariance log determinant. Whiten the saved earlier
residuals with that operator. Report each coordinate's mean, RMS and lag-1,
lag-5 and lag-20 correlation, plus the total quadratic cost. Preserve the
input and source hashes with the output.

This is a diagnostic. Fitting 26 calibration parameters changes the
distribution of the residuals, so no off-the-shelf white-noise threshold or
95% coverage claim follows from these numbers. A calibrated rejection rule
would require separate known-answer tests that repeat the full fitting step.
No receiver position after report 599 and no reserved ESA flight group may be
read by the worker. This study makes no Earth-model decision.

## Qualification and allowance

Pass generated covariance/innovation checks, source-bound qualification and
the finite reboot-recovery control before launch. Run exactly two tasks, one
per prespecified error law. Each has one original start, no optimizer
evaluations, at most 500,000 native calls and 1 billion packet/query visits.
Use two workers of one numerical thread each and a 7,200-second cooperative
wall cap. Preserve charges and failures. An unchanged interrupted task may
resume only through separately frozen, finite technical recovery; a completed
task is never rerun. The seven reserved ESA groups stay unopened.
