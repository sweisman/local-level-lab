# Long forecast scores with linear memory

The structured calculation reproduced all **80 saved ESA path scores**
using both three coordinates and north/east alone. The largest difference
from the dense calculation was below **2.5 × 10⁻¹¹** in squared
standardized score. Earlier height observations still enter the
conditioning in both calculations. [Dense comparison](ESA_HEIGHT_ROLE_RESULT.md)

| Later positions in generated size check | Full and north/east operators together | Dense three-axis factor alone |
| ---: | ---: | ---: |
| 2,048 | 11.1 MB | 302 MB |
| 4,096 | 21.1 MB | 1,208 MB |

The table counts stored matrix entries. It omits temporary working memory
and shows the dense allocation size without constructing that factor.
The structured calculation keeps a small state and updates it as it scores
each position. It retains correlations across axes and time, including
the unobserved later height's effect on the uncertainty of north and east.
Small generated checks verify the calculation against a separate dense
reference and check that a saved state continues the score across blocks.

All six technical tasks passed with 86 charged calculations and no new
navigation fits. Aircraft error calibration and independent prediction
coverage remain open. The seven reserved ESA groups stayed closed.

[Fixed plan](ESA_STRUCTURED_AXIS_SCORE_PLAN.md) ·
[All scores and storage counts](esa-structured-axis-score.json) ·
[Verified replay bundle](esa-structured-axis-score-evidence/replay.zip)
