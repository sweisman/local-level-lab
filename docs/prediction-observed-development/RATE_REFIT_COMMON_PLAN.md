# Saved-only diagnosis of shared ESA prediction error

Use only the six sealed forecasts from the completed ESA rate-refit study and
the same saved 1,200 development receiver positions used for its scoring.
Keep the original 800 earlier / 400 later split and all six task identities.
No raw file, reserved confirmation group, new fit or changed accuracy rule is
part of this diagnostic.

At each receiver time, convert forecast-minus-receiver position into north,
east and up errors using the existing shared coordinate-error routine. For
each IMU error law separately, average the three rate-method error vectors to
form the **shared residual**. Subtract that shared vector from each method's
error to measure the spread attributable to changing rate assignment. Report
RMS and maximum horizontal/height quantities for the earlier and later parts,
and in successive fixed 100-epoch blocks. Keep both laws separate; they are
alternative error assumptions, not independent flight replications.

This is a descriptive decomposition on one development recording. A large
shared residual can rule out rate assignment as a sufficient explanation for
the observed miss, but cannot identify its physical cause. Do not select a
method from later errors, infer a calibrated confidence level, alter the
frozen six-fit result or open any of the seven reserved ESA groups. Record the
closed-study hashes, receiver-score hash and diagnostic source hash with the
output so the calculation can be repeated.
