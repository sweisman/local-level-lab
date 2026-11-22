# Check whether completing the ESA error fits changes the result

The [saved-point audit](ESA_JOINT_PERSISTENCE_STOPPING_RESULT.md) found
feasible downhill directions in all eight donor fits. This comparison tests
whether taking those remaining steps changes the two missed forecasts.

Use the same eight folds, six donor windows per fold, two input conventions,
six bounded log parameters and Gaussian loss. Start once per fold at the
previously saved setting. Use the checked analytic gradient with L-BFGS-B.
Allow at most 128 joint value-and-gradient calls per fold, two one-thread
workers and a 180-second cooperative deadline. Charge each call before
it runs. Verify task-level technical recovery before launch and retain
all original capped fits and any new failures.

First qualify the new call path on generated interior and bound-active
problems with known optima. Check that value and derivative requests share
one charged calculation, and that an exhausted allowance preserves the
best scored point. On the recorded donors, report the saved and updated
losses, projected derivatives and stopping codes. Require the original
projected gradient tolerance of 0.00001 and a verified score replay to
call the donor refit complete. Keep the fitted settings sealed before
reading the two omitted windows from each fold.

Score the omitted windows using the original reference and report changes
in their standardized errors and log scores. Keep incomplete donor fits
separate, even if their best scored setting is useful to inspect. Report
whether both input conventions place all eight windows inside the original
reference. All windows are on the established development flight. This
comparison authorizes no new trajectory fit and no access to reserved
flights. It does not qualify the error law for other aircraft or flights.
