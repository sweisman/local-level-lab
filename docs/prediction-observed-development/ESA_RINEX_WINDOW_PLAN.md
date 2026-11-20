# Prepare raw receiver observations for the existing ESA comparison

Use the AIR1 RINEX file from development recording 187. Match receiver
times to the already frozen [400/120 comparison](ESA_400_120_MODEL_MATRIX_PLAN.md).
Keep the later coordinates sealed. Retrieve complete half-second raw
epochs from GPS week seconds 388214.5 through 388734.5, inclusive. Use
the GPS time scale on both sources. Retain the observation records without
interpolation or changes to satellite values.

The live listing gives `air10706a.23o` a size of 363,446,705 bytes.
Reuse the verified 256 KiB prefix for the original header. Use at most
16 additional 256 KiB byte-range probes to locate the starting epoch,
then at most nine contiguous 1 MiB ranges to cover the window. Verify that
each response has the requested length. Record the exact byte offsets,
per-range SHA-256 hashes, retained record count and header. Use a
45-second limit per request and at most three attempts per range. Retain
verified earlier reads on interruption
and leave the other ESA groups closed.

This preflight verifies source, time coverage and raw signal availability.
It performs no new position solve or inertial fit. A later comparison
needs pinned orbit, clock and bias products, an independently qualified
kinematic solver, and a common-error assessment because the two solutions
would use the same antenna. Preserve the existing 400/120 forecast results.

[RINEX standards](https://igs.org/wg/rinex/) ·
[ESA campaign](https://earth.esa.int/eogateway/campaigns/airborne-quantum-gravimetry-airquantumgrav-2023)
