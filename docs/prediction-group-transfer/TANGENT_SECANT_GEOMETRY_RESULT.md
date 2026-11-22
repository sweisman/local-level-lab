# The trial-tangent solver passed the disc check and stalled on zero-field globe

All four fits finished in about 200 seconds. The two reference fits passed.
The new solver passed on the generated disc and stopped before convergence
on the generated zero-field globe. The previously completed specified-field
globe check also passed, giving two passing geometries across the three short
controls. [Frozen plan](TANGENT_SECANT_GEOMETRY_PLAN.md) ·
[First geometry](TANGENT_SECANT_FLIGHT_RESULT.md)

| Generated case | Reference evaluations | Trial-tangent evaluations | Training cost gap | Largest withheld position difference | Matched result |
| --- | ---: | ---: | ---: | ---: | --- |
| Zero-field globe, 200 Hz nominal clock | 31 | 21 | 0.679 | 4.46 m | Failed |
| Disc, 300 Hz header clock | 77 | 63 | 0.000000000597 | 0.0000155 m | Passed |

The zero-field globe candidate reached training cost 26.835. The reference
reached 26.156. The candidate predicted a cost reduction on its final attempted
step, but the evaluated cost rose by 0.108. The fresh stopping check found
that the estimate still had room to improve. Its position errors were within
the separate physical limits. The disc candidate passed both checks and used
37 curvature updates. Neither candidate needed separate derivative probes.

The saved trace shows that the last accepted zero-field step was evaluation
11. All nine subsequent trial steps raised the cost. Refreshing the curvature
estimate produced a full step that raised the cost by about 148,000. Halving
that step seven times reduced the increase to 0.108. This suggests testing a
fallback that changes the search direction when repeated step reductions fail.
The solver remains a research option. This study read zero original or
reserved flight records.
[Verified result data](tangent-secant-geometry-result.json)
