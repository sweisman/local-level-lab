# One fitted trajectory, three GNSS receivers

The two sealed ESA IMU fits used only the first 400 `air1` positions. Their unchanged, pre-conditioning trajectories are compared here with `air1` and two other PPP exports at the same earlier times. The other receivers were adjusted to the `air1` epoch using their reported velocity and submillisecond time offset. No later receiver report, protected flight, new fit or IMU packet was used.

| Saved error law | Receiver | Fitted-minus-receiver north/east/up RMS (m) |
| --- | --- | ---: |
| increment | air1 | 0.777/0.992/0.473 |
| increment | mosaic03 | 0.785/0.980/0.450 |
| increment | pwrpak7 | 0.782/0.997/0.446 |
| point | air1 | 0.777/0.992/0.473 |
| point | mosaic03 | 0.785/0.980/0.450 |
| point | pwrpak7 | 0.782/0.997/0.446 |

The fitted trajectory misses each receiver by roughly 0.8 m north and 1.0 m east RMS, while the receivers differ from one another by centimetres. These are **training** residuals from the raw fitted trajectory, not predictions on unused times; the separate early-only conditioning step changes the later forecast. The receivers share an antenna and may share PPP errors. Close agreement cannot establish absolute accuracy, a prediction-error law or an Earth-model decision.

[Fixed method](PARALLEL_GNSS_FIT_PLAN.md) · [Detailed result](PARALLEL_GNSS_FIT_RESULT.json).
