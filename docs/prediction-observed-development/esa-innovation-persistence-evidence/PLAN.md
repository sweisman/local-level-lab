# Test persistent forecast errors after turns

Use the eight saved forecast windows and the original four turn-and-steady
pairs from ESA recording 187. Keep both inertial error descriptions. The
[earlier audit](ESA_INNOVATION_TRANSFER_RESULT.md) found that errors after a
turn can stay correlated even under the original temporal model. This test
asks whether a longer memory learned on other windows predicts their errors.

Keep each fold's [saved donor-only variances](ESA_AXIS_INNOVATION_SCALE_RESULT.md),
the two added covariance components and the forecast means. In the ordered
north, east and height innovations, compare the original covariance with two
alternatives. One uses a common exponential memory. The other uses the existing
15-second angular-exposure response to blend quiet and motion transition
coefficients. Each transition uses the exact time between reports. Scale the
unpredictable part of the transition so that every standardized state retains
unit variance. The new rule changes correlation, and the variance of each
individual innovation stays fixed. These are score coordinates, with no claim
that the fitted memory belongs to a specific sensor.

Choose from 0, 0.25, 0.5, 1, 2, 4, 8, 16, 32 and 64 seconds. Zero resets
the state at each report. Check all 100 pairs of quiet and motion memory
settings. For the common-memory rule, use only the ten equal settings. In
each fold minimize the joint negative log score on the six donor windows.
Break ties by the smaller quiet and then motion settings. Save both choices
before opening the two omitted receiver position inputs. Score the later
windows without changing the variance settings, memory or mean.

Use the unchanged joint squared-error reference. A development pass requires
better combined omitted log score than the saved diagonal covariance
and all eight windows inside the reference under both error descriptions.
The reference is a working check. The eight windows are from one recording.

Freeze eight folds, two one-thread workers, 180 seconds and 100 proposed
settings per fold. Allow two original-score operations per window and six
final comparisons per fold. Bind the existing qualified technical recovery.
Use no original recordings, reserved flights, new fits or propagation.
