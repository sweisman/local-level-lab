# Noisy timing probe: saved values

**Eight objective points were saved, but the study did not pass its technical wrapper.**
The worker used the wrong key for its final abstention field. The terminal failure
and all charges remain recorded. This report audits the sealed point values only;
it does not relabel the study as passing.

The reconstructed IMU samples and receiver rows matched the original failed case.
The probe kept every other fitted parameter fixed and varied only the timing offset.
At points immediately before the packet boundary, all 79 receiver queries switched
packets; immediately after it, none switched.

| Timing shift | Packet changes | Actual cost change | Local predicted change |
|---|---:|---:|---:|
| saved point (0 s) | 0 | 0 | 0 |
| boundary before 1ns (-4.28688302e-08 s) | 79 | 1.72772729e-09 | 1.68009251e-09 |
| boundary after 1ns (-4.08688302e-08 s) | 0 | 1.52152779e-09 | 1.49924517e-09 |
| minus 100ns (-1e-07 s) | 79 | 1.2582376e-08 | 1.10802318e-08 |
| plus 100ns (1e-07 s) | 0 | 1.40119027e-08 | 1.3988938e-08 |
| minus 10us (-1e-05 s) | 79 | 0.000125456801 | 0.000125199851 |
| plus 10us (1e-05 s) | 0 | 0.000125490711 | 0.000125490724 |
| full timing component (-0.000962753928 s) | 79 | 1.16183062 | 1.16180536 |

The full timing-only shift raises the objective by 1.16183; the local tangent predicts a rise of 1.16181.
The two-minute noisy timing-only calculation therefore follows its tangent even
across packet changes. Packet switching by itself does not explain the original
failed *joint* calibration/timing step. That coupled direction remains the
specific numerical question; the failed 24-case stopping gate is unchanged.

This is one generated software diagnostic, not an observed-aircraft result,
uncertainty calibration or Earth-model decision. No solver start or forecast was run.

[Original failed-case diagnosis](NONLINEAR_DIAGNOSIS.md) ·
[Finite plan](TIMING_PROBE_PLAN.md) · [Technical result](NONLINEAR_RESULT.md)
