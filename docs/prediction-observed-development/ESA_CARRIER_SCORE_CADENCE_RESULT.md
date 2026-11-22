# Which carrier errors can a ground receiver check?

The existing Nuuk 30-second observations provide **effectively zero direct
leverage** on the part of the two-minute ESA score that can change between
those very same ground samples. Ideal one-second coverage on the same flight
could reach **99.98%** of the signed carrier weight norm used in the score.
This calculation explains what the denser recording would add. It does not
measure the precision of that recording.

| Ground coverage | Share of score-weight norm visible | Share remaining invisible |
| --- | ---: | ---: |
| Actual three 30-second intervals | Effectively 0% | 100% |
| Ideal four 30-second intervals starting at the aircraft window boundary | 19.47% | 98.09% |
| Ideal one-second intervals throughout the window | 99.98% | 2.08% |

The visible and invisible components are perpendicular. Their squared shares
add to one. The percentages apply to the geometry of the score and do not
describe the fraction of actual aircraft error removed or measured.

The actual ground receiver measures a total range change between consecutive
samples. A range change inside that interval can return to its starting value
and leave the total unchanged. The earlier carrier weights were constructed for
position errors that return to zero at the actual ground times. After matching
the common satellites and removing the receiver clock, the signed residual
from the actual ground intervals projects onto those weights at less than
\(10^{-17}\) of the score gap, including with the earlier fitted multiplier.
That numerical zero reflects the sampling geometry. It supplies no bound on
error between the samples. The ideal 30-second grid starts six seconds earlier
than the actual ground samples. Its shifted boundaries reveal some of the
variation inside the actual intervals.

The [frozen calculation](ESA_CARRIER_SCORE_CADENCE_PLAN.md) used 2,496 signed
range values from 240 carrier pairs, six passing software tests and all four
planned operations. No original measurements were reopened, no fits ran,
and the reserved ESA flights remained sealed. The [result](esa-carrier-score-cadence-result.json)
records the projected weights and the signed station terms. Its SHA-256 is
`3c992f6a0c5200651f89e0c773a6b56f2b94b1261a9c751495cee0c9bcde1bda`.
