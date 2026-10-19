# What this diagnostic establishes

All **18 exact-trajectory controls passed**, covering three physical models and
six motion profiles. The independent Cartesian and local-navigation calculations
agree to about 1.8 × 10⁻¹⁵ m/s² in required force. That is software agreement,
not the precision or accuracy of a real instrument.

Stationary controls correctly retain indistinguishable force magnitudes. Some
moving controls produce different magnitudes under different models; the largest
incorrect-model RMS mismatch in this matrix is about **0.030 m/s²**.

This is an important limit on interpretation: with exact calibration and an
exact receiver trajectory, acceleration and coordinate geometry alone can
separate some generated cases. It does not show how much of the real-data result
comes from those inputs. The full gyro/acceleration comparison cannot be divided
into percentages by subtracting these diagnostic scores.

The two changing body attitudes give the same magnitude residual, so this
calculation does not borrow a heading or fused orientation. It still depends
on the candidate coordinate metric, the stated background term, apparent
gravity and acceleration calibration. A mismatch of this size is not a detection
threshold or evidence that actual calibration errors are smaller.

No recordings were read, no model was fitted to observed data, and the existing
53-stretch findings remain unchanged. The fixed background rate in these
controls is a declared software input, not a measured solar/sidereal rate.

[Complete control matrix](README.md) · [Receiver-derivative groundwork](DERIVATIVES.md) ·
[Remaining gate](NEXT_PLAN.md).
