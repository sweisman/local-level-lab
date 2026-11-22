# Test the trial calculation on two saved aircraft fits

Use the two IMU8 fits from the same recorded training stretch. The
specified-field globe fit passed the stopping check and saved a forecast.
The zero-field disc fit reached 30 evaluations and failed the stopping
check. It had no forecast. The comparison must reproduce both outcomes.

Use the original training packets, earlier GPS fixes, clock, starting
parameters, bounds and weighting. Keep the limit of 30 solver evaluations.
Allow up to 60 native training calls per fit, with each kind charged before
execution. Allow one forecast for the globe control and compare it with the
sealed forecast. The solver receives no later GPS fixes. Run two workers with
one thread each under a 30-minute limit.

Require exact equality of the complete solver records and of the control
forecast. The zero-field disc's failure remains a failure. This check
qualifies the calculation for these archived cases. It does not complete
the missing four-model scientific comparison.

[Aircraft preflight results](MATCHED_OBSERVED_NUMERICAL_RESULT.md) ·
[Generated full-fit result](MATCHED_TRIAL_FITS_RESULT.md).
