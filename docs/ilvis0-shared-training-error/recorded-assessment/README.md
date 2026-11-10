# Recorded receiver training-prefix assessment

All **18 predeclared calculations completed** on one numerical thread in 300 seconds. They used 292 earlier, one-second receiver fixes from one development recording. The frozen study made **zero Earth-model fits and zero original IMU reads**. Every calculation returned an exact, outward-rounded upper scale bound under its declared Gaussian error law. Every scientific decision remains **abstain**: the study has not shown that either error law describes the receiver or that its bound covers aircraft prediction errors.

The table gives the upper multiplier on the declared receiver-error standard deviation. It is not a measured position error or an Earth-model score. The three reference degrees were selected before this run; lower values with a more flexible reference do not establish better coverage.

| Assumed correlation time | Reference degree | North | East | Height |
| --- | ---: | ---: | ---: | ---: |
| 10 s | 3 | 3.792 | 2.074 | 0.290 |
| 10 s | 5 | 2.193 | 1.230 | 0.291 |
| 10 s | 7 | 0.273 | 0.440 | 0.285 |
| 300 s | 3 | 9.046 | 5.059 | 1.175 |
| 300 s | 5 | 6.517 | 3.656 | 1.185 |
| 300 s | 7 | 0.899 | 1.571 | 1.165 |

The same 292 fixes and fixed local coordinate chart were used in every row. Each axis was assessed separately. The calculation includes declared white, correlated, common-offset and drift components; it tests two correlation times and three polynomial reference spaces. The scale bound is conservative **conditional on the specified Gaussian covariance law and fixed reference space**. No result chooses a covariance law from the Earth-model ranking.

The frozen manifest is `6c3fe95d2419a5f952b2893b3d55a9d429c8b30380fb71a52fcd3c8ae44eb62b`; its completed summary is `b54aec81376defe04f6b54d1db815605883c544b460a0e701e0899418cc80e11`. The 292-fix input is `5dfabe1f4562cef21581177d8578a8ed1db065420caa72def8a03b776aa6126c`. The attached receipt verifies all copied artifacts and frozen source.

**Next gate:** test the receiver-error law against observations independent of the polynomial training fit and quantify prediction coverage. Until that passes, these multipliers are a sensitivity result, not an operational uncertainty threshold.
