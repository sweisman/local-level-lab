# Archived satellite clock changes do not match the shared-motion example

The [constructed shared displacement](ESA_SHARED_MOTION_GAP_RESULT.md)
would need a **4.88 mm RMS** satellite-range correction per half-second
pair to cancel its geometric signature on the common satellite set.
The archived broadcast-to-final satellite clock change was **0.58 mm
RMS** on the same set. Their signed patterns were nearly orthogonal
(cosine **−0.043**). Applying the clock change left **4.94 mm RMS**
unaccounted for in this comparison.

| Quantity | Half-second range RMS (mm) |
| --- | ---: |
| Required to cancel the constructed displacement, all used satellites | 4.67 |
| Required on the common set with final clock data | 4.88 |
| Archived satellite clock change, common set | 0.58 |
| Required correction minus archived clock change | 4.94 |
| Original carrier residual after fitting position and receiver clock | 3.77 |

The comparison uses 240 frozen carrier pairs with 2,736 original
satellite observations across the pairs. The 2,496 comparisons on the
common set exclude G17, which lacks final clock samples. Each pair
removes a common range term to account for the freely estimated
receiver clock change. The broadcast transmit times and the unshifted
carrier solution stay fixed. This isolates the geometric signature and
the recorded satellite clock update.

The original residual is measured after fitting a position. It cannot
serve as a bound on a range error that could move that position. The
archived clock update alone does not supply the required pattern.
Remaining clock or orbit error, the atmosphere, and antenna or tracking
errors still need separate evidence. This calculation does not establish
independent airborne accuracy or change the shape comparison.

Seven software checks passed. The study completed all 241 bounded
operations. No receiver or inertial fit ran and no reserved flight opened.

[Frozen plan](ESA_SHARED_MOTION_CARRIER_PLAN.md) ·
[Signed range differences and completion record](esa-shared-motion-carrier-result.json)
