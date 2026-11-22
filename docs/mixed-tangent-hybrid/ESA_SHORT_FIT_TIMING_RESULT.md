# Selective derivatives speed up both short recorded ESA fits

The selective method completed both recorded ESA cases using less than half
the process CPU of the wide method. Both methods converged, took the same
number of fit evaluations within each pair, and kept every fitted parameter.
The two fits in each pair agreed within the frozen cost and path tolerances.

| Matched globe case | Fit evaluations per method | Wide fit CPU | Selective fit CPU | Wide/selective ratio |
|---|---:|---:|---:|---:|
| Specified field, short receiver error policy | 18 | 197.15 s | 69.51 s | 2.84× |
| Zero field, persistent receiver error policy | 9 | 104.32 s | 47.67 s | 2.19× |

The median ratio was **2.51×**, above the frozen 1.25× criterion. The largest
difference between matched predicted positions was 1.42 nanometres. The fit
CPU times include setup after kernel availability and exclude compilation and
forecast propagation. The complete calculation including both excluded stages
also ran faster, with CPU ratios of 2.80× and 2.15×.

The test used 120 training positions and 30 additional query times from a
previously prepared ESA development window. Later receiver positions stayed
withheld. This verifies the speed gain on the short prefix for the two globe
settings. The full recorded 20-minute path and the wide-only disc path have
separate timing and qualification requirements.

Both pairs completed on two one-thread workers in 291 seconds. They used 58
charged native operations and returned no errors. The benchmark preserves the
earlier numerical and scientific results.

[Frozen method](ESA_SHORT_FIT_TIMING_PLAN.md) ·
[Measured CPU and wall times](esa-short-fit-timing-result.json) ·
[Verified run evidence](esa-short-fit-timing-evidence/README.md)
