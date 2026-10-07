# The axis change and vertical acceleration discrepancy

This six-file investigation is complete. All source hashes and strict packet checks passed.
It explains the changed axis mapping and provides a strong timing explanation for the earlier
acceleration failures. It does not change the scientific acceptance rule.

The recordings contain repeated legacy setup messages. Their candidate mounting-angle fields
reproduce all six previously fitted gyro mappings. The four older recordings use a 90-degree
yaw setting; the 2015 recording uses −90 degrees; the 2017 recording uses 90-degree roll and
pitch settings. The last change accounts for its different axis mapping without choosing a
mapping from the gyro outcome. Hardware and firmware identity therefore do not define a
complete installation configuration.

The public [Applanix interface document](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
describes frame rotations and modern Message 20. These files instead contain legacy Message 1.
Its field offsets are empirically inferred and independently checked against the saved gyro
comparisons, not an authoritative legacy field table. Complete packet bytes and unsupported
layouts are preserved. Samples before the first logged setting are excluded from this check;
later settings are not silently assigned to earlier measurements.

The principal acceleration discrepancy comes from the interval used to turn each increment
into a rate. Header intervals fluctuate around 5 milliseconds. Dividing by each fluctuating
interval creates a substantial apparent change in the large gravity-related vertical reading.
Across the complete streams, interval variation is about 12.4–13.6 microseconds, with adjacent
interval correlations between −0.45 and −0.56. The mean intervals remain within about 10 parts
per million of 5 milliseconds, with no gaps above 7.5 milliseconds. This pattern is consistent
with timestamp jitter around a steady sensor clock, but does not directly measure that clock.

An explicit alternative uses a fixed 200 Hz period. Under that hypothesis:

- All six three-axis accelerometer checks pass, including chronological scale checks, at
  **3.38 × 10⁻⁵ metres/second per integer velocity increment**.
- Vertical disagreement falls by **76–595 times** compared with the measured-header interval.
- Five of six gyro checks pass at **0.4 arcsecond per integer angle increment**.
- The remaining gyro chronological check misses the existing 0.1% scale tolerance narrowly:
  one half estimates a scale ratio of 0.9989858. That failure remains recorded.

Both normalizations are retained. No measured timestamp is replaced, no science data is
interpolated, and no automatic decoder selects whichever normalization happens to pass.
The decimal velocity scale is an empirical hypothesis, not a discovered manufacturer table.
The evidence supports the increment interpretation and favors fixed-period normalization
against the fused reference; physical integration timing still needs independent confirmation.

We also tested the candidate sensor-to-reference offset. Applying the simple rigid-body
lever-arm acceleration formula worsens agreement at each supported derivative timescale,
for either sign. The sparse 2017 navigation stream cannot support that high-rate correction
and is labeled unsupported. This is evidence against that simple correction as an explanation
for these residuals; it does not establish that Applanix applies no lever-arm processing.

The reusable investigation is `analysis/lll/ilvis0_installation.py`; its launcher is
`analysis/tests/ilvis0_installation_worker.py`. The worker finished and released its lock.
Durable reports live in `data/ilvis0-installation-clock-20261007/`. This evidence directory
contains the source snapshot, source/input/environment manifest, complete compressed report
and per-file CSV inventory. Thirty focused tests passed, including corrupt framing, inferred
versus documented layouts, setting epochs, clock jitter, sparse derivatives and resume checks.
Older failure reports remain intact, and all 232 originals remain preserved.

Next: establish the sensor integration-clock convention and remaining gyro scale discrepancy
before enabling a physical conversion across more files. Recorded corrections, sensor identity
and independently established orientation still need investigation. Group 1 remains a fused
decoder reference, not independent evidence of Earth rotation or shape; no Earth-model fit ran.
