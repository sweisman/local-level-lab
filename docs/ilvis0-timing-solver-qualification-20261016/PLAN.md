# Qualifying a packet-aware timing step

The [completed native diagnostic](../ilvis0-timing-derivative-v2-20261016/RESULTS.md)
found the failed primary and repeat on opposite sides of a common packet boundary:
about 23 ns before and 72 ns after. Their full and half coupled corrections cross
that boundary, predict lower objective values and instead increase the actual
objective. The same physical models, measurements and final numerical thresholds
remain in force.

The separate candidate retains the hybrid solver's full bounded Gauss–Newton
attempt. After rejection, it solves local steps restricted to the current packet
interval. It also evaluates neighboring intervals using a 1 ns offset beyond
their nearest boundaries, rebuilding the native Jacobian there before solving.
The overall physical timing bound stays ±0.15 seconds. Only actual objective
improvements meeting the existing acceptance ratio can be accepted. Every native
call counts against the same per-start allowance; the final fresh undamped
stationarity, cost and physical-position checks are unchanged.

Software qualification covers the preceding 48 controls plus independent
piecewise timing examples, minima exactly at knots, a genuine cusp, known native
motion with an unknown time offset, feasibility and call accounting. A genuine
cusp with nonzero one-sided gradients must remain unresolved under the unchanged
smooth stationarity gate, even if its correct minimum is recovered.

The once-charged qualification batch freezes **67 tests**, source/environment
hashes and a ceiling of **11,000 software evaluations**. Use four total
numerical threads and a ten-minute timeout; no observed fits or archive reads.
Development tests are ordinary local checks, separate from the sealed qualification.

Only a fully passing software batch permits the separate matched observed trial:
four starts (the failed primary, its predetermined perturbed repeat and the two
existing controls), at most 200 calls per target start and 40 per control, plus
two diagnostic calls each: **488 native calls maximum**, no retries. Reuse the
five hashed passing primary companions from the prior matched trial. Freeze that
trial independently before launch. Each complete comparison requires both controls,
the primary, the scheduled repeat and all companion fits. No wider rollout or
changed scientific label follows from software qualification alone.
