# Force magnitudes did not qualify the platform clock

All three planned excerpts reproduced their earlier byte probes and the
1,024 Hz relative clock. The first excerpt failed to identify a unique
offset to the independently timed 10 Hz force record. The two later
excerpts independently pointed to the same candidate, which is useful for
checking the horizontal channels.

| Excerpt | Best correlation | Next separated peak | Candidate offset to UTC seconds |
| --- | ---: | ---: | ---: |
| First, preselected anchor | 0.462 | 0.455 | 50,431.967 s |
| Second | 0.848 | 0.419 | 38,474.267 s |
| Third | 0.637 | 0.383 | 38,474.267 s |

The original [timing plan](ESA_GIRAFE_PLATFORM_TIMING_PLAN.md) required
the first excerpt to exceed 0.70 with a lead of at least 0.10 over the
next separated peak. Because it failed, the two later peaks remain a
candidate hypothesis. The [horizontal-channel check](ESA_GIRAFE_PLATFORM_COMPONENT_TIMING_PLAN.md)
uses the saved excerpts to test that hypothesis independently of their
total force magnitudes. The earlier decision remains a failed timing
qualification.

The terminal [receipt](esa-girafe-platform-timing-result.json) has SHA-256
`89f55710675bf6f16e8413916581644ab6a267c276072fbf8e26b4dcb8b8df86`.
It preserves all seven charged operations, three completed comparisons and
zero model fits. The machine evidence records the exact captured byte
hashes and keeps the source ranges in the local authorized data directory.
Future acquisition and analysis use the separate
[bounded transfer workflow](ESA_GIRAFE_PLATFORM_TRANSFER.md).
The [portable evidence bundle](esa-girafe-platform-timing-evidence/bundle.zip)
preserves the original frozen analysis and its charges.
