# Runtime profiles of generated prefixes

2/2 shortened bounds completed; both retain their profiling outcomes.

| Candidate | Function | Calls | Cumulative seconds |
|---|---|---:|---:|
| Specified field | ilvis0_source_native_v2.py:enclose | 1 | 4.2616 |
| Specified field | ilvis0_source_native_v2.py:_increment | 188 | 1.8837 |
| Specified field | ilvis0_compiled_transport.py:_operation | 7052 | 1.0482 |
| Specified field | ilvis0_compiled_bounds.py:vector | 8563 | 0.87553 |
| Specified field | ilvis0_compiled_bounds.py:_array | 137182 | 0.66082 |
| Specified field | ilvis0_compiled_transport.py:_finish | 14103 | 0.60877 |
| Specified field | ilvis0_rounded_body_interval_v2.py:bound | 94 | 0.58199 |
| Specified field | ilvis0_compiled_bounds.py:norm | 28677 | 0.51313 |
| Specified field | ilvis0_source_value_stream.py:append | 94 | 0.50106 |
| Specified field | fromnumeric.py:all | 195447 | 0.49391 |
| Specified field | ilvis0_compiled_transport.py:scale | 2069 | 0.48447 |
| Specified field | ilvis0_source_reference.py:affine_radius | 564 | 0.44319 |
| Zero field | ilvis0_source_native_v2.py:enclose | 1 | 7.5632 |
| Zero field | ilvis0_source_native_v2.py:_increment | 188 | 3.3492 |
| Zero field | ilvis0_compiled_transport.py:_operation | 7052 | 1.8384 |
| Zero field | ilvis0_compiled_bounds.py:vector | 8563 | 1.5329 |
| Zero field | ilvis0_compiled_bounds.py:_array | 137558 | 1.1813 |
| Zero field | ilvis0_compiled_transport.py:_finish | 14291 | 1.0928 |
| Zero field | ilvis0_rounded_body_interval_v2.py:bound | 94 | 1.04 |
| Zero field | ilvis0_compiled_bounds.py:norm | 29053 | 0.92125 |
| Zero field | ilvis0_source_value_stream.py:append | 94 | 0.88957 |
| Zero field | fromnumeric.py:all | 196011 | 0.88455 |
| Zero field | ilvis0_compiled_transport.py:scale | 2069 | 0.85924 |
| Zero field | ilvis0_source_reference.py:affine_radius | 564 | 0.79235 |

Charged 2/2 bounds and 1024/1,024 world/source packet-steps. Elapsed 17.60 seconds.

Reserved 256/256 source-reference steps and 256/256 rounded body bounds.

These profiles locate implementation costs on shortened generated inputs. They preserve the clock range and use new physical-domain proofs; they do not transfer full-history training information to changed sources. Profiler times are not full-recording performance or numerical-qualification evidence. No native trajectory, observation, LP or optimizer was used.

[Frozen scope](PLAN.md) · [Saved-baseline comparison](../ilvis0-source-range-preflight/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
