# Height-aware bounds on generated histories

The shared-prefix predictor passed all four generated cases. The largest
position remainder at the longest query, 39.875 seconds, was **0.315 mm**.
For the ESA development comparison, **4.03 cm** is a sufficient uniform
bound over a much longer history if the earlier fit error is bounded too.
[Where the target comes from](SHAPE_REMAINDER_METRES_RESULT.md).

| Model | Packet size | Largest remainder at the four query times, mm |
| --- | ---: | ---: |
| Zero-field globe | 5 ms | 0.000150 · 0.000209 · 0.000329 · 0.000574 |
| Zero-field disc | 5 ms | 0.000101 · 0.000149 · 0.000244 · 0.000439 |
| Zero-field globe | 250 ms | 0.003863 · 0.011554 · 0.051236 · 0.314619 |
| Zero-field disc | 250 ms | 0.002987 · 0.008897 · 0.039893 · 0.248223 |

The 5 ms grid ends at 0.7975 seconds. The 250 ms grid extends elapsed time
with coarse packets. It does not reproduce the recording's packet density.
All 16 reference positions agreed with compiled forecasts within 1.5 nm.
The reported remainders covered the three prescribed calibration probes
at each query within the frozen comparison allowance. At the longest
query, path propagation accounted for over 95% of the largest remainder.
The [generated plan](SHAPE_GRAVITY_HISTORY_V3_PLAN.md) used four bound calls
and 16 compiled forecast calls on one thread. It read no aircraft
recordings and performed no fits.

The [initial setup](SHAPE_GRAVITY_HISTORY_PLAN.md) rejected the runner's
task fields before any numerical calls. The [second setup](SHAPE_GRAVITY_HISTORY_V2_PLAN.md)
reached the initial-force guard. Its zero-centred case exceeded the
stored cap by less than 2 × 10⁻¹⁸ m/s², so it produced no propagated
bounds. Both sets of terminal results and charges were kept. The completed
check used a nonzero reference and the same box width and acceptance limits.

The next test needs a conservatively rounded initial-force cap that works
at any tested reference, followed by a longer generated history with the
packet density and earlier-fit constraints used for the aircraft comparison.
The work ledger also identifies a cost to remove before scaling up. Each
case used 163 shared-prefix and tail propagation steps, but its four
reports made 640 visits to the same 160 packets to compute force
integrals. Indexing those integrals once per record would avoid a full
scan for each report. The [shared calculation](SHARED_FORCE_INTEGRALS.md)
now passes the exact comparison against the original scans.

The [zero-centred retest](SHAPE_INITIAL_FORCE_RESULT.md) uses the
outward-rounded cap and the shared calculation. All four cases
that previously stopped at the initial-force guard now pass.

[Setup evidence](shape-gravity-history-v1-evidence/README.md) ·
[Initial-force rejection evidence](shape-gravity-history-v2-evidence/README.md) ·
[Completed evidence](shape-gravity-history-v3-evidence/README.md).
