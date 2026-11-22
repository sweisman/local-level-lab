# Test the reversing accelerometer correction against earlier positions

Use the three sealed increment-law fits from the profiled-processing
400/120 development comparison. Verify their original earlier
whitening factors and controlling archive. Set their X-axis
accelerometer bias to +0.10 m/s², the endpoint that reversed the
gyro-direction comparison. First keep every other parameter fixed.
Then use the saved earlier weighted Jacobian to propose one bounded
least-squares adjustment of all other parameters. Keep the X bias
fixed and every parameter within its original box. Save the affine
prediction and whether the linear solve settled.

Use the archived scalar integrator to replay each baseline and both
endpoint points. Apply the unchanged earlier weights and compare the
increase in squared loss with the existing 0.01 earlier loss limit.
Report earlier horizontal and height RMS too. The affine adjustment
is a proposal. A failed exact replay does not exclude other
adjustments in the nonlinear model. The stationary-disc trajectory
in this archive is distinct from the disc given a matched local
field in the gyro direction test.

Use one numerical thread, three bounded linear proposals at no more
than 100 iterations each and nine predefined scalar replays. Retain
all outcomes and charge replays before computation. Use the 520
pre-existing query times, but read no later receiver positions.
Do not start a new full fit or open any reserved recording.

[Endpoint reversal](ESA_GYRO_DIRECTION_CALIBRATION_RESULT.md) ·
[Previous archived scalar replay](ESA_LINKED_PHYSICAL_REPLAY_RESULT.md)
