# One-second sampling would shift the test from gaps to position accuracy

Exact position anchors at one-second intervals would make the gaps much
harder to exploit. With 120 ideal anchors, an error that vanishes at every
anchor would need at least **71.2 m/s² RMS acceleration** to span the saved
score gap. The same bound with the four verified 30-second anchors is
**1.66 mm/s²**. The continuous-motion minimum for those four anchors was
1.876 mm/s². [Verified four-anchor calculation](ESA_NUUK_BETWEEN_SAMPLES_RESULT.md)

| Position schedule | Interior anchors | Lower bound on RMS acceleration with exact anchor positions | Uniform error per coordinate at the anchors that could span the gap through interpolation alone |
| --- | ---: | ---: | ---: |
| Verified permanent Nuuk times | 4 | 0.00166 m/s² | 2.32 m |
| Ideal, complete one-second grid | 120 | 71.2 m/s² | 4.65 cm |

The bound adds the two contributions. Divide the allowed position error by
the value in the last column, divide the allowed RMS acceleration by the
value in the preceding column, and add the two fractions. A sum below one
would keep the tested affine score from crossing zero under the fixed
endpoint assumption. Use the unrounded coefficients in the result when
applying the bound.

The large acceleration requirement comes from timing. The saved score times
are very close to the integer GPS seconds. With complete, accurate anchor
positions, most of the score's leverage on errors falls close to those
anchors. A real ground receiver measures satellite ranges. We still need to
check overlap and quantify the resulting aircraft position error before
using the ideal-grid bound. These are design requirements for one fixed score
and window. The calculation used the nominal grid and sealed score evidence.
[Nuuk Museum file](ESA_GROUND_REFERENCE_AVAILABILITY.md)

The study completed both bounded operations. Seven focused tests passed.
There were no new fits or reserved flight reads.
[Frozen plan](ESA_GROUND_GRID_SCORE_PLAN.md) ·
[Verified result](esa-ground-grid-score-result.json)
