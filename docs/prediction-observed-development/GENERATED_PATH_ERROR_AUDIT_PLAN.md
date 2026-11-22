# Saved generated-path error audit

## Question

The two sealed 600-report generated fits have nearly white fitted training
errors but fail their known-truth trajectory screen. Is that discrepancy
mainly noisy receiver position, or does the fitted physical path depart from
the known generated path?

## Fixed inputs and method

Read only the closed `generated-esa-600-innovation-null-v1-20261117` study.
For each of its two laws, verify the saved forecast and known-truth scores,
then score the saved noisy **training receiver** positions against the same
known truth using the existing physical-coordinate scoring function. Compare
receiver-to-truth, fitted-to-truth, and fitted-to-receiver errors on the same
600 epochs. Report their per-axis and horizontal RMS, early/late path errors,
and count fitted parameters at declared bounds. Do not regenerate truth,
fit again, alter either outcome, or read the ESA aircraft or reserved groups.

This is a diagnostic decomposition of two generated examples. It cannot
identify a unique physical cause, calibrate a tail probability, or qualify
observed-aircraft uncertainty. The failed 10 m gate remains failed.
