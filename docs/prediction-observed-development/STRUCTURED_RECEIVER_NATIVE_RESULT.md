# Receiver calculation with the physical IMU Jacobian

The dense and structured receiver calculations agree on one actual airborne
training prefix. This check used **120 earlier receiver positions**, 24,049
recorded IMU packets and a single native prediction at the zero calibration
point. The native calculation returned all **26 physical calibration
derivatives**. Both error calculations then whitened the *same* coordinate
residual and derivative columns under the declared `h1_v3_tau60` law.

| Comparison | Difference |
|---|---:|
| Largest whitened receiver residual | 9.77×10⁻¹⁴ |
| Largest whitened physical Jacobian entry | 1.43×10⁻¹¹ |
| Relative fitted-objective calculation | 8.30×10⁻¹⁶ |
| Log determinant | 0 |

The separately frozen [study plan](STRUCTURED_RECEIVER_NATIVE_PLAN.md)
specified one native call and 2,885,880 packet visits. The study completed
1/1 tasks and charged exactly those limits. Its manifest SHA-256 is
`396800eb2f4dd39cd233cc10522ba05e3653ac37ac0684b44c3a43a3792d55db`;
all nine source-bound software and recovery checks passed. Later receiver
positions were unavailable to the study, and no fit or model decision was
made. The source freeze, training input and result are retained under
`data/ilvis0-structured-receiver-native-v1-20261118`.

This establishes equivalence of the **receiver whitening calculation and
physical Jacobian at one point**. It does not show that the assumed
covariance describes the real aircraft errors, that a fitted solution is
stable, or that a long recording predicts later positions. Those are the
next separate checks.
