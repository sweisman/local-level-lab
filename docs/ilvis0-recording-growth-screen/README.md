# Fifty-second bound growth on complete four-minute inputs

6/6 numerical cases passed; elapsed 2309.82 seconds.

| Candidate / processing | Numerical checks | Bound time | Largest unshared radius | Largest full-domain radius |
|---|---|---:|---:|---:|
| Specified-field globe / zero | Pass | 322.91 s | 1152 m | 72253 m |
| Specified-field globe / profiled | Pass | 324.45 s | 1154.4 m | 72259 m |
| Zero-field globe / zero | Pass | 311.84 s | 901.31 m | 72004 m |
| Zero-field globe / profiled | Pass | 364.32 s | 899.21 m | 72005 m |
| Flat disc / zero | Pass | 443.40 s | 353.25 m | 71471 m |
| Flat disc / profiled | Pass | 520.22 s | 396.37 m | 71518 m |

Radii use the original frozen coordinate comparison frame. Full-domain radii include the shared terms as well as approximation error; they are not confidence intervals or measured aircraft errors. The entire original broad parameter domain is retained, with no orientation-sector selection or training constraints. The original clock offset remains fixed.

Charged 24/24 native queries, 6/6 bounds and 2592000/2,592,000 logical steps. Unused reservations remain charged. No original-aircraft observations, LP or optimizer were used.

This is a nominal fifty-second runtime/growth screen on complete four-minute inputs. Even a passing numerical screen does not establish useful four-minute prediction bounds, an uncertain clock or observational coverage. The earlier four-minute failures and all 53 aircraft findings stay unchanged.

[Frozen scope](PLAN.md) · [Format checks](../ilvis0-recording-adapter-controls/README.md) · [Next gates](../ilvis0-three-source-complete/NEXT_PLAN.md).
