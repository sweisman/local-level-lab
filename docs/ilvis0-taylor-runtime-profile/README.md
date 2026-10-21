# Source-derivative propagation costs

2/2 shortened bounds completed.

| Processing | Function | Calls | Cumulative seconds |
|---|---|---:|---:|
| Fixed-zero removal | ilvis0_taylor_native.py:enclose | 1 | 14.441 |
| Fixed-zero removal | ilvis0_source_taylor.py:bound | 94 | 4.1987 |
| Fixed-zero removal | ilvis0_taylor_native.py:_increment | 188 | 4.1417 |
| Fixed-zero removal | ilvis0_batched_body_interval.py:bound | 94 | 2.3461 |
| Fixed-zero removal | ilvis0_source_taylor.py:append | 94 | 1.8644 |
| Fixed-zero removal | ilvis0_geographic_bounds.py:_result | 13290 | 1.8614 |
| Fixed-zero removal | fractions.py:forward | 209751 | 1.8358 |
| Fixed-zero removal | ilvis0_source_reference.py:affine_radius | 564 | 1.807 |
| Fixed-zero removal | ilvis0_source_derivative_intervals.py:mean_value_radius | 94 | 1.7711 |
| Fixed-zero removal | ilvis0_batched_source_values.py:append | 94 | 1.6684 |
| Fixed-zero removal | ilvis0_taylor_native.py:_rates | 188 | 1.6089 |
| Fixed-zero removal | ilvis0_batched_bounds.py:vector | 8563 | 1.5037 |
| Fixed-zero removal | fractions.py:__new__ | 179367 | 1.4956 |
| Fixed-zero removal | ilvis0_batched_transport.py:_operation | 7052 | 1.4324 |
| Fixed-zero removal | ilvis0_local_step_bounds.py:__post_init__ | 39728 | 1.4016 |
| Profiled removal | ilvis0_taylor_native.py:enclose | 1 | 15.966 |
| Profiled removal | ilvis0_source_taylor.py:bound | 94 | 4.6151 |
| Profiled removal | ilvis0_taylor_native.py:_increment | 188 | 4.5496 |
| Profiled removal | ilvis0_batched_body_interval.py:bound | 94 | 2.5984 |
| Profiled removal | ilvis0_source_taylor.py:append | 94 | 2.1561 |
| Profiled removal | fractions.py:forward | 209751 | 2.0777 |
| Profiled removal | ilvis0_geographic_bounds.py:_result | 13290 | 2.0115 |
| Profiled removal | ilvis0_source_reference.py:affine_radius | 564 | 1.9954 |
| Profiled removal | ilvis0_batched_source_values.py:append | 94 | 1.9303 |
| Profiled removal | ilvis0_source_derivative_intervals.py:mean_value_radius | 94 | 1.9288 |
| Profiled removal | ilvis0_taylor_native.py:_rates | 188 | 1.7463 |
| Profiled removal | fractions.py:__new__ | 179419 | 1.6648 |
| Profiled removal | ilvis0_batched_bounds.py:vector | 8563 | 1.6545 |
| Profiled removal | ilvis0_batched_transport.py:_operation | 7052 | 1.5757 |
| Profiled removal | ilvis0_local_step_bounds.py:__post_init__ | 39728 | 1.5183 |

Elapsed 50.30 seconds; charged 2/2 bounds and 2048/2,048 logical steps.

These are new 128-packet diagnostic inputs with their own physical-domain proofs. They do not reuse full-history training certificates or retry failed regions. Profiler costs are not full-recording speed, qualified prediction widths or observational uncertainty. No aircraft data, native trajectory or fitting was used.

[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
