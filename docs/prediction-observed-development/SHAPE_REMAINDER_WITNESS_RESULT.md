# Where the nonlinear error in calibration grows

The two exact replays closest to the original earlier fit-loss limit
passed it after reducing each calibration step to 98% of its selected
size. The full-size steps slightly exceeded the 0.01 limit. At the
two passing points, the earlier nonlinear remainder norms were below
**0.000086** and the error in the later shape direction was below
**0.000022** per candidate, in the standardized units of the respective
scores.

| Zero-field candidate | Change | Exact increase in earlier loss | Earlier remainder norm | Later projected remainder |
| --- | --- | ---: | ---: | ---: |
| Globe | Original step | 0.0100019 | 0.0000889 | 0.00000679 |
| Globe | 98% of original step | 0.0096059 | 0.0000854 | 0.00000654 |
| Disc | Original step | 0.0100620 | 0.0000552 | 0.00002207 |
| Disc | 98% of original step | 0.0096636 | 0.0000530 | 0.00002153 |

With the larger loss allowances from the
[headroom calculation](SHAPE_REMAINDER_HEADROOM_RESULT.md), the disc
remainder reached 0.160 at the trial chosen for an assumed limit of 0.1.
The largest tested trial reached 0.388. Both exceeded the original loss
allowance by a wide margin. The proposed limit of 0.1 therefore fails
on the full local box. These points leave it open as a bound on the
smaller region that fits the earlier data. A proof needs to enclose that
region without excluding any truly feasible calibration point.

Both baseline replays reproduced the sealed trajectories within one
nanometre. All eight probes were retained. The run charged ten scalar
passes, including the two baselines, with no new fits, later receiver
positions or reserved data. The four related software checks passed.

[Frozen plan](SHAPE_REMAINDER_WITNESS_PLAN.md) ·
[All eight exact checks](shape-remainder-witness-result.json) ·
[Verified archive](shape-remainder-witness-evidence/README.md)

Manifest SHA-256
`199aa293a49cf8738c3f6161e78165fe10f948f0d1e3f36f156e62224d26ad60`.
