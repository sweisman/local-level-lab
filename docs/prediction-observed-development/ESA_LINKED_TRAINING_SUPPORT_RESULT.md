# Earlier GPS narrows the calibration range on the ESA development flight

The 400 earlier GPS positions substantially narrow how far calibration
changes can move the two forecasts toward each other. With all 51
physical and shared-error coordinates retained, the bound fell from
**687.23 to about 103 standardized units** when the assumed earlier
unshared error was zero. The saved globe–disc difference is **25.41
units**. The tighter bound is still too wide to establish that the
separation survives the allowed changes.

| Assumed earlier unshared error norm per candidate | Upper bound on reduction, globe | Upper bound on reduction, disc | Combined upper bound |
| ---: | ---: | ---: | ---: |
| 0 | 52.635 | 50.395 | 103.030 |
| 0.1 | 52.149 | 50.555 | 102.703 |
| 1 | 52.967 | 51.962 | 104.928 |

Each row uses its own certified direction. The small reversal between
the first two rows reflects the tightness of those particular bounds.
The feasible region itself grows as the assumed error increases.
The earlier unshared error is a hypothetical input. The calculation
leaves later unshared error outside the bound.

Both cases completed under the [frozen plan](ESA_LINKED_TRAINING_SUPPORT_PLAN.md).
One of the six numerical direction searches did not report convergence.
Its direction still produced an upper bound because the proof uses an
outward projection and a box maximum that hold for any finite direction.
The check started no new trajectory fits and used no later receiver
positions. The reserved ESA flight groups remain closed.

The shared coefficients vary independently within their bounds here.
The [preceding force-map calculation](ESA_FORCE_SCORE_RESULT.md) shows
that physically linking those coefficients can tighten their contribution.
The next check is to apply that physical constraint inside the earlier-fit
region, then verify the unshared errors over the full recording.

[Sealed inputs, source and results](esa-linked-training-support-evidence/README.md).
