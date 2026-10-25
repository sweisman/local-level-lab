# Frozen matched-noise execution

The [construction qualification](nonlinear-construction-qualification/README.md)
passes 21 checks. The separately tested lifecycle must also pass before this
new run is prepared. The completed covariance benchmark is not restarted.

Use two workers with one numerical thread each, reserving two threads for the
existing full test job. Allow two hours of cooperative runtime, no retries,
no optimizer starts and no original or protected data reads. Each worker may
build one noise bridge and one scalar-value library. Each operator is limited
to 64 MiB. Missing charged build assets must stop rather than cause a new build.

| Setting | Native-call allowance | Conservative packet-query visits | Normal variates |
|---|---:|---:|---:|
| Increments, 120 s | 36,184 | 278,496,119 | 10,375,776 |
| Rate points, 120 s | 36,184 | 278,496,119 | 6,919,872 |
| Increments, 1,200 s | 361,265 | 28,080,361,200 | 103,756,992 |
| Rate points, 1,200 s | 361,265 | 28,080,361,200 | 69,197,088 |

Calls include packetwise covariance construction and 65 full value propagations
per setting: one nominal plus four amplitudes for each of 16 seeds. Packet-query
visits retain the existing conservative full-record accounting convention; they
are not a claim about the native loop's actual operation count.

Construction also allows exactly 794,642 nominal samples, 792,000 intervals
and 64 matched seed/settings controls overall. Seeds are shared across settings
for comparison; do not call those 64 independent replications.

Preserve compilation bindings, all construction charges, draw hashes, nominal
coordinates, conditional standard deviations, every matched error curve and
each pass/failure. The fixed test is in the [method plan](NONLINEAR_PLAN.md).
No outcome changes aircraft-model labels, accuracy screens or confirmation access.
