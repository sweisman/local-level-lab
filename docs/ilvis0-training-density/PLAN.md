# Full-history training-density diagnostic

Compare five earlier observation epochs with 292, using all six qualified
generated eight-minute inputs. The dense epochs are seconds 2 through 293;
the original five epochs are an exact subset. Predict at 438 seconds.
Preserve all 27 physical columns, their original broad box and ±1-second clock.
Evaluate the native Jacobian at the original zero expansion. This is an affine
geometry diagnostic, not coverage over the nonlinear clock/calibration domain.

One native batch call per identity returns 293 positions/Jacobians. A separate
endpoint call must agree exactly in position and every derivative column.
Check the aggregate packet-boundary counter against the actual timestamps;
this does not qualify smooth derivatives at the boundaries.

For both training sets, use the same ±1 m affine position-change constraint.
Make six LP proposals per set. Independently verify each dual support endpoint
using exact arithmetic. Preserve sparse certificates when adding dense rows.
The software diagnostic succeeds when every native and certificate check
passes; whether linear ranges meet 20 / 20 / 50 m is a separate reported result.
Neither outcome qualifies nonlinear prediction, observation errors or aircraft
significance. No future measurements enter the constraints.

| Resource | Per identity | Total maximum |
|---|---:|---:|
| Kernel calls | 2 | 12 |
| Queried epochs | 294 | 1,764 |
| Conservatively charged packet visits | 28,224,000 | 169,344,000 |
| LP proposals | 12 | 72 |
| Exact support checks | 36 | 216 |

Use the existing support routine's one-second LP limit, a 600-second cooperative
study ceiling and one worker with one numerical thread. Reserve other active
allocations. No interval bounds, aircraft reads, model-fit starts, retries,
process signals or allowance expansion.

Freeze source, recipe, environment, compiler and hash references to the already
frozen generated inputs. Verify those input hashes before reading them. Reuse
the documented duration-study files rather than duplicate them in each study.
Require the completed twelve-case native remainder qualification before launch.
Publication must use sealed results without repeating native or LP work.
