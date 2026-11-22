# The fallback did not qualify for use on aircraft fits

Two of three generated flight comparisons passed. The zero-field globe took
134 training tangent attempts and reached the 210-second wall limit before
saving a fit or forecast. Its sealed reference passed in 31 evaluations.
The failure leaves the three-geometry qualification open.
[Frozen plan](TANGENT_SECANT_FALLBACK_PLAN.md) ·
[Verified result data](tangent-secant-fallback-result.json)

| Generated case | Reference evaluations | Candidate evaluations | Accepted fallback trials | Largest withheld position difference | Matched result |
| --- | ---: | ---: | ---: | ---: | --- |
| Specified-field globe | 10 | 69 | 1 | 0.00000351 m | Passed |
| Zero-field globe | 31 | 134 attempted | Unavailable | Unavailable | Wall limit |
| Disc | 77 | 71 | 0 | 0.0000155 m | Passed |

Each of the two completed forecasts agreed with its sealed reference well
within the original 0.10 m position tolerance. The fallback added 20
evaluations on the specified-field globe and eight on the disc compared
with the earlier trial-tangent runs. On the disc, none of the eight
fallback steps was accepted. The zero-field time limit left no final trace
from which to count accepted steps. [Previous matched results](TANGENT_SECANT_GEOMETRY_RESULT.md)

The established trust-region solver remains the reference. This fallback
adds work even on the short cases it passes and failed the case it was
designed to recover. The study used generated data only and leaves all
aircraft results and reserved flights untouched.
