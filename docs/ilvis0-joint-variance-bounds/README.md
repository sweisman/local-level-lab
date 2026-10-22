# Variance bounds that include clock uncertainty

The observation-error allowances now have a checked source of variance bounds
under the declared linear noise model. The calculation uses exact fractions
and rounds each returned value outward. It covers every time in the supplied
clock interval, rather than assuming the nominal timestamp is exact.

**12 focused checks pass; 86 component/regression checks pass together.** A
six-case staged integration matrix also passes using these bounds and a nonzero
clock offset in every case. One component check covers all 147 later epochs of the earlier prediction
plan, plus the five training epochs used in the current feasibility study.
That checks the noise allowances, not the physical-model predictions at those
147 epochs.

The calculation preserves the fixed integration origin, receiver drift origin,
correlated receiver components, accelerometer noise and the coupling of gyro
noise into position error. It rejects covariance matrices with even a small
negative direction instead of rounding that direction away.

The receiver/IMU error law remains supplied. A valid variance calculation does
not establish unknown processing behavior, nonlinear noise propagation or the
correct aircraft noise spectra. A noise scale estimated under a nominal clock
also needs justification before it can cover every permitted clock offset.

The running long-record study, its original error allowance and its finite
budget are unchanged. No new aircraft fits have started.

[Derivation](MATHEMATICS.md) ·
[Simultaneous allowances](../ilvis0-gaussian-allowances/README.md) ·
[Remaining V01 checks](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)
