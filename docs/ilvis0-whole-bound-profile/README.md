# Whole-bound cost profile

Full bound completed: **yes**.

Wall time: 94.25862045004033; process CPU time: 90.641194792; CPU/wall ratio: 0.9616223360710263.

| Function | Calls | Cumulative seconds |
|---|---:|---:|
| ilvis0_direct_range_preflight.py:evaluate | 1 | 94.2558 |
| ilvis0_direct_native.py:enclose | 1 | 89.4315 |
| ilvis0_direct_native.py:_increment | 2942 | 24.1005 |
| ilvis0_direct_source_taylor.py:bound | 1471 | 23.9675 |
| ilvis0_direct_source_taylor.py:append | 1471 | 17.7427 |
| ilvis0_dyadic_source_taylor.py:bound | 1471 | 12.2706 |
| ilvis0_dyadic_source_taylor.py:append | 1471 | 12.1707 |
| ilvis0_direct_source.py:radius | 1471 | 11.2655 |
| fractions.py:forward | 2921836 | 11.2109 |
| ilvis0_batched_source_values.py:append | 1471 | 10.9450 |
| ilvis0_geographic_bounds.py:_result | 206070 | 10.7463 |
| ilvis0_direct_native.py:_rates | 2942 | 9.4747 |
| ilvis0_batched_bounds.py:vector | 133870 | 8.8401 |
| ~:<built-in method builtins.max> | 2774930 | 8.6300 |
| ilvis0_batched_transport.py:_operation | 110327 | 8.4574 |
| ilvis0_local_step_bounds.py:__post_init__ | 614325 | 8.0705 |
| ilvis0_dyadic_body_interval.py:bound | 1471 | 7.6244 |
| fractions.py:__new__ | 2217600 | 7.4119 |
| ilvis0_batched_transport.py:__init__ | 91480 | 7.1218 |
| ilvis0_geographic_bounds.py:__post_init__ | 259211 | 6.6781 |

Charged 1/1 bound and 14400/14,400 logical steps. Profiler overhead is included; setup and compilation also appear in the function list. This diagnostic supplies no replacement certificate, speed qualification or aircraft result. If unfinished, the original finite allowance remains spent.

[Frozen scope](PLAN.md) · [Failed timing comparison](../ilvis0-midpoint-runtime/INTERPRETATION.md).
