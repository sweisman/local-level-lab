# Test the IMU8 receiver correction without a full gradient pass

The first study completed IMU21. Its IMU8 calculation reached its time cap
after beginning the gradient pass and before testing any receiver correction.
Retain the IMU21 result and preserve the stopped IMU8 record and its charge.

Use the exact original IMU8 receiver material. Calculate gradients only
for inequalities with a positive saved deficit. They propose a correction,
with at most 64 gradients and 64 projection steps. Verify the resulting
single receiver history by recomputing all 4,864 force intervals, including
every inequality that was already satisfied. Retain violations regardless of
which inequalities were used for the proposal. All calibration, motion and
uncertainty assumptions stay as stated in the original experiment.

Use one worker, one thread, three charges and a 120-second cooperative
limit. The IMU21 calculation is carried forward from its sealed result.

[First calculation](SHARED_FORCE_WITNESS_PLAN.md)
