# Runtime profiles of generated prefixes

2/2 shortened bounds completed; both retain their profiling outcomes.

| Candidate | Function | Calls | Cumulative seconds |
|---|---|---:|---:|
| Specified field | ilvis0_cached_native.py:enclose | 1 | 17.157 |
| Specified field | ilvis0_cached_native.py:_increment | 188 | 12.1 |
| Specified field | fractions.py:forward | 758375 | 4.2543 |
| Specified field | fractions.py:__new__ | 884570 | 4.0197 |
| Specified field | ilvis0_cached_transport.py:matrix_vector | 1134 | 3.8882 |
| Specified field | ~:<built-in method builtins.sum> | 76539 | 3.2638 |
| Specified field | ilvis0_cached_transport.py:_combine | 7528 | 2.8756 |
| Specified field | ilvis0_cached_transport.py:scalar_product | 1692 | 2.8115 |
| Specified field | ilvis0_directional_values.py:_product_bounds | 18666 | 2.6547 |
| Specified field | ilvis0_cached_transport.py:_norm | 34040 | 2.622 |
| Specified field | ilvis0_cached_transport.py:add | 2257 | 2.5899 |
| Specified field | ilvis0_relative_rotation.py:__post_init__ | 3580 | 2.4792 |
| Zero field | ilvis0_cached_native.py:enclose | 1 | 17.248 |
| Zero field | ilvis0_cached_native.py:_increment | 188 | 12.092 |
| Zero field | fractions.py:forward | 751767 | 4.2816 |
| Zero field | fractions.py:__new__ | 872646 | 4.0191 |
| Zero field | ilvis0_cached_transport.py:matrix_vector | 1134 | 3.9723 |
| Zero field | ~:<built-in method builtins.sum> | 74880 | 3.2364 |
| Zero field | ilvis0_cached_transport.py:scalar_product | 1692 | 2.761 |
| Zero field | ilvis0_directional_values.py:_product_bounds | 18666 | 2.7188 |
| Zero field | ilvis0_cached_transport.py:_combine | 7528 | 2.7164 |
| Zero field | ilvis0_relative_rotation.py:__post_init__ | 3580 | 2.517 |
| Zero field | ilvis0_cached_transport.py:add | 2257 | 2.5149 |
| Zero field | ilvis0_cached_transport.py:_norm | 34416 | 2.4376 |

Charged 2/2 bounds and 512/512 bound packet-steps. Elapsed 35.77 seconds.

These profiles locate implementation costs on shortened generated inputs. They preserve the clock range and use new physical-domain proofs; they do not transfer full-history training information to changed sources. Profiler times are not full-recording performance or numerical-qualification evidence. No native trajectory, observation, LP or optimizer was used.

[Frozen scope](PLAN.md) · [Saved-baseline comparison](../ilvis0-transport-range-preflight/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
