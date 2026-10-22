# Isolating the remaining curvature improves every fixed probe

Keeping the known calibration terms and correcting only the remaining
curvature improves **all twelve generated probes**.

| Processing case | Shared-source RMS mismatch | After residual correction |
|---|---:|---:|
| Zero removal | 9.07 m | 0.64 m |
| Profiled removal | 45.35 m | 3.28 m |

The largest remaining coordinate mismatches are about 4.0 m and 17.9 m.
These numbers compare the same six saved epochs. No coefficients or calibration
points were fitted to obtain the correction.

This identifies a more useful approximation than averaging the whole
derivative. It does **not** yet provide a guaranteed prediction range. The
derivatives at known generated probes are diagnostic information; the actual
aircraft calibration remains unknown.

The next mathematical step is a uniform error bound for this residual
correction. It must handle packet-clock boundaries rather than assume that
derivatives are smooth everywhere. All parameter regions and unsupported cases
must remain accounted for before new aircraft prediction fits.

[Verified calculation](README.md) · [Next mathematical step](NEXT_PLAN.md) · [Current work](../NEXT_STEPS.md)
