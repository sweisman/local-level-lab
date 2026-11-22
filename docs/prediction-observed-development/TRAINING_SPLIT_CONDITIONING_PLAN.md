# ESA 600/200 conditional forecast

This second development task follows the sealed 600/200 fits. For each law
whose earlier fit passes its numerical checks, it rebuilds the declared IMU
and receiver error operator over the same 800 report times. It verifies that
the first 600 reports reproduce the saved training cost and covariance, then
uses only those earlier receiver errors to predict a correction and nominal
uncertainty for reports 600–799.

The worker receives no scored receiver values, does no fitting, keeps all 26
calibration columns, and cannot change either input-error law. Each law has a
separate ceiling of 450,000 native calls and one billion packet visits. At
most two one-thread workers run within a 7,200-second study wall limit.
Task-level technical recovery must qualify before launch. A failed fit
abstains and is not rerun to improve its numerical result. Scoring against
receiver reports 600–799 occurs only after these artifacts close. This is
retrospective development on recording 187, not independent validation or
calibrated coverage. Seven other ESA groups remain reserved.
