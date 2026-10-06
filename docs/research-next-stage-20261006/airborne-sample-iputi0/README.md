# First airborne navigation sample

This IPUTI0 sample comes from an airborne Antarctic survey. It contains processed navigation
outputs: position, velocity and orientation. It provides aircraft-motion information but no
independent raw gyro channels, so no Earth-model discriminator has been applied.

`inputs/` preserves exactly the five supplied files. The inspection record gives their byte
counts and hashes. The navigation table preserves packet offsets and exact time-tag bytes;
it deliberately supplies no interpreted timestamps because the binary time representation
and correspondence with the separate clock file are unresolved.

The clock spans about 25½ minutes with approximately one entry per second. Decoded horizontal
speed is about 70–94 m/s. There are 1,527 valid status packets and 1,527 valid navigation packets.
An apparent header fails its payload checksum at offset 10,800. Searching within that rejected
candidate finds valid frames 11 bytes later. Those unframed bytes remain in the original; no
repair or interpolation was performed. Checksum and byte-order conventions are inferred
from the sample. Fixed-point scaling comes from the supplied descriptions.

Status bit meanings, binary time-tag interpretation, timezone, processing corrections and
mount orientation need documentation before using these values quantitatively. Navigation
heading and attitude may depend on an assumed Earth model. Differentiating them does not
produce an independent raw gyro measurement.

Reproduce into a new output directory, leaving this preserved inspection intact:

```sh
/home/sweisman/venv/bin/python analysis/tests/inspect_iputi0_sample.py --input-dir docs/research-next-stage-20261006/airborne-sample-iputi0/inputs --output-dir /tmp/iputi0-reinspection
```

The inspector reads only five explicit filenames. Three small software checks cover corrupted
candidate recovery, signed field scales, truncated packets and relative clock units. No full
suite, synthetic flights, calibration or model decisions were run for this inspection.

Dataset: [IceBridge IMU L0 Raw Inertial Measurement Unit Data, Version 1](https://nsidc.org/data/iputi0/versions/1),
DOI 10.5067/7K31MCH5XXZA.
