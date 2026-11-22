# Match the platform clock against the separate iMAR recorder

Two of three saved GIRAFE excerpts matched the iMAR accelerometer at the
proposed clock offset. The middle excerpt fell short, so the proposed clock
did not pass the [frozen check](ESA_GIRAFE_PLATFORM_IMAR_FORCE_PLAN.md).

Both instruments were on the same aircraft. The check used changes in total
force magnitude after 1.1 seconds of averaging. GIRAFE observations had
already suggested the offset. The iMAR observations did not select it.

| Saved excerpt | Correlation at proposed time | Best nearby correlation | Best shift |
| --- | ---: | ---: | ---: |
| First | 0.941 | 0.968 | −0.1 s |
| Middle | 0.116 | 0.284 | +0.1 s |
| Last | 0.957 | 0.957 | 0.0 s |

All three nearby peaks occur within 0.1 seconds of the proposed time. The
first and last track closely, while the middle peak is weak even at its best
shift. The middle excerpt also shows smaller force changes, with roughly half
the variation measured by iMAR over the same period. It matched the separate
timed GIRAFE vertical output well after averaging. These results leave open
whether platform motion or the different instruments' responses explains the
disagreement. The candidate vertical channel gives the same overall pattern.

The single local task completed with 13 charged operations, zero native model
fits and zero reserved-group reads. Absolute timing and gyroscope channel
interpretation remain open. The [verified score receipt](esa-girafe-platform-imar-force-result.json)
contains all 41 shifts for each comparison.

[Source, inputs and execution receipts](girafe-platform-imar-force-evidence/README.md) ·
[Verified reproduction bundle](girafe-platform-imar-force-evidence/bundle.zip)
