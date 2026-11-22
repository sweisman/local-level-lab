# First local-uncertainty task stopped on a missing saved derivative

The one-task ESA development study ended **terminal**, with no covariance
result and no Earth-model decision. It rebuilt the full error operator and
passed the saved early covariance replay. The next step rejected its input:
the earlier saved forecast contains 1,200 positions and 800 training
differences, but **no forecast Jacobian**. The study plan had incorrectly
treated that derivative as retained.

The task charged its one permitted start, 450,000 native calls and one
billion packet visits. Its failure, source, inputs, environment, qualification
and charges remain sealed. It must not be rerun under the same identity.
The local-uncertainty calculation therefore has **not** yet been tested on
the observed recording. This is a technical input failure, not evidence that
fitted-parameter uncertainty is small or large.

A corrected, separately charged calculation must generate the fitted-point
forecast tangent during the same bounded task, verify its positions against
the saved forecast and its **whitened training Jacobian** against the saved
fit, then apply the existing calibration-uncertainty calculation. It should
reuse the full error operator already needed for covariance, without building
another training operator. The seven reserved ESA groups remain unopened.
