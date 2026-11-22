# A candidate interpretation for the GIRAFE angular-rate columns

Reading the last three columns as **radians per second**, in their original
order and signs, best predicted changes in the first excerpt's measured
force direction. The same convention modestly improved tenth-second
predictions in both held-out excerpts. At one second its errors were larger
than assuming no change in all three excerpts.

| Excerpt | Tenth-second error assuming no change | Tenth-second error using rates | One-second error assuming no change | One-second error using rates |
| --- | ---: | ---: | ---: | ---: |
| First, used to choose the convention | 581 | 560 | 681 | 687 |
| Middle, held out | 530 | 513 | 646 | 754 |
| Last, held out | 616 | 588 | 881 | 1,055 |

All errors are angular RMS in arcseconds. There were 111 tenth-second pairs
and 11 one-second pairs per excerpt. After removing the mean from each
tenth-second change series, squared direction error fell by **6.7–9.9%**.
On the first excerpt the next-best convention flips the last sign and
gives 566 arcseconds, compared with 560 for the selected convention. The best
degrees-per-second convention gives 580 arcseconds.

The [frozen screen](ESA_GIRAFE_PLATFORM_RATE_PLAN.md) tried 96 unit and
axis combinations on the first excerpt and carried the winner unchanged to
both holdouts. It uses only force direction and angular-rate candidates
from the same platform and its relative clock. Force direction also changes
with acceleration, and turning around the force axis is hard to see. The
one-second errors and close alternative sign leave the full rate mapping
unqualified. Fine alignment with iMAR and the relationship of the moving
platform to the airframe also remain open. A low-speed ground comparison or
a documented channel map could supply a stronger check.

The task completed all 98 comparisons. It used the three saved source
ranges, zero model fits and zero reserved-flight reads. The [verified ledger](esa-girafe-platform-rate-result.json)
preserves every score and the selected convention.

[Source and execution receipts](girafe-platform-rate-evidence/README.md) ·
[Verified reproduction bundle](girafe-platform-rate-evidence/bundle.zip)
