# One-second GPS comparison with the Nuuk Museum receiver

The EarthScope station day matched all **520** one-second timestamps within
ESA development flight 187's saved GPS window. In the two-minute scoring
interval, all **120** one-second steps passed the checks, with **9–11** common
GPS satellites per step after carrier screening. The comparison covered
**99.98%** of the norm of the saved carrier weights.

| Range residual | RMS on 1,247 matched satellite steps | Signed share of the saved score gap |
| --- | ---: | ---: |
| Aircraft | 4.79 mm | +0.35% |
| Nuuk Museum | 6.71 mm | −2.53% |
| Aircraft minus Nuuk Museum | 8.10 mm | +2.88% |

The RMS measures the typical range discrepancy on those matches. The
signed score measures the component that affects this specific model
comparison. The small signed difference leaves open errors common to both
receivers, errors specific to the aircraft antenna, and absolute position
error. This is one development flight. It does not qualify the confirmation
error model. The next comparison can test whether a correction learned
from earlier observations improves the later aircraft ranges.

The original download was 44,704,731 bytes. Its SHA-256 was
`d975a3c042079457b4cde7311e941d3cd1fea684e6394ed796db86a84c383af4`.
The intake verified the archive, RINEX 2.11 header and timestamps. The
legacy signal labels leave exact tracking-code compatibility open.

Eleven software tests passed under a new source binding. The previous
qualification stopped preparation before any scored task started because
four dependencies had changed. The historical qualification is retained.
The sealed comparison completed all 121 prescribed checks. It ran no
model fits and opened no reserved aircraft data.

[Coverage receipt](esa-nkar-ground-coverage.json) ·
[Sealed score report](esa-nkar-ground-score-result.json) ·
[Fixed method](ESA_NKAR_GROUND_SCORE_PLAN.md) ·
[Replay commands](ESA_NKAR_INTAKE_READY.md) ·
[EarthScope station day](https://data.earthscope.org/archive/gnss/highrate/1-Hz/rinex/2023/187/nkar/).
