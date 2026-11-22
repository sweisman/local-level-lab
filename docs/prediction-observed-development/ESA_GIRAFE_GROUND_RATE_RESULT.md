# The Greenland stop reveals a consistent timing shift

All three clips favored matching the platform force with iMAR **0.1 seconds
earlier** than the proposed clock offset. Correlations at that shift were
0.953–0.973. Correlations at the fixed offset fell short in all three clips.
The candidate platform rate convention also increased force-direction errors
at both tested separations. The combined [frozen check](ESA_GIRAFE_GROUND_RATE_PLAN.md)
therefore passed on zero of three clips.

| Ground target, GPS second | Correlation at proposed time | Best correlation | Second-highest correlation | Best shift |
| ---: | ---: | ---: | ---: | ---: |
| 385574 | 0.160 | 0.953 | 0.524 | −0.1 s |
| 386250 | 0.038 | 0.968 | 0.531 | −0.1 s |
| 386927 | −0.043 | 0.973 | 0.527 | −0.1 s |

| Ground target, GPS second | Tenth-second error assuming no change | Tenth-second error using rates | One-second error assuming no change | One-second error using rates |
| ---: | ---: | ---: | ---: | ---: |
| 385574 | 677 | 687 | 1,322 | 1,373 |
| 386250 | 1,130 | 1,150 | 2,315 | 2,351 |
| 386927 | 614 | 616 | 1,366 | 1,514 |

Direction errors are angular RMS in arcseconds. The test used the original
platform axes and radians per second, fixed by the earlier airborne screen.
On the ground, the squared errors also grew after removing the mean changes.
Aircraft acceleration, platform movement and sensor response still affect
this check. The time shift could reflect the recording clocks, a difference
in sensor delay or both. All three clips helped reveal the shift, so it
remains a candidate for independent timing validation. The angular-rate
mapping remains unqualified.

The [saved airborne lag scores](ESA_GIRAFE_PLATFORM_IMAR_FORCE_RESULT.md)
give correlations of 0.968, 0.108 and 0.850 at the same earlier shift. This
post hoc check still leaves the middle airborne excerpt unexplained.

The six original range reads delivered the exact declared byte counts. One
check read and two longer reads had final FTP response timeouts. The independent
512-byte overlaps matched, and all three ranges passed the saved clock-phase
check. The local task completed all 13 charged operations with zero model fits
and zero reserved-flight reads. The [machine-readable result](esa-girafe-ground-rate-result.json)
binds the transfer receipt and saves every lag score and direction error.

[Source and execution receipts](girafe-ground-rate-evidence/README.md) ·
[Verified reproduction bundle](girafe-ground-rate-evidence/bundle.zip)
