# The GIRAFE recorder has a consistent clock and variable-width rows

Three small reads from the opened ESA flight returned all 29,568 requested
bytes. The fixed-width check failed because the fourth column sometimes
takes one more character. Each byte range begins inside a row. The later
check kept every complete interior row and retained the acquisition-edge
fragments with the unaltered source bytes.

| File byte offset | Complete rows | First complete time tag | 77-byte rows | 78-byte rows |
| ---: | ---: | ---: | ---: | ---: |
| 465,076,150 | 127 | 6588.2949 | 119 | 8 |
| 930,152,377 | 127 | 12477.3906 | 88 | 39 |
| 1,395,228,527 | 127 | 18366.0664 | 105 | 22 |

The 381 complete interior rows and the 212-row prefix have seven finite
numeric columns and ordered time tags. They share one clock phase
consistent with 1,024 samples per second and four-digit rounding. This
establishes the clock pattern at the sampled locations. A fixed byte
stride misses the last sampled time by about 26 seconds. Seek by reading
time tags at complete row boundaries.

The clock's UTC or GPS offset and the physical channels remain open.
Matching the platform's force changes to the separately time-tagged motion
records could establish that offset and help identify the channels. It
would allow a second sensor to check the direction measurement on this
flight. The platform's movement and sensor spacing would remain part of
the comparison.

## Evidence

The [initial probe](esa-girafe-platform-probe-result.json) preserves all
three failed fixed-width interpretations and their charged reads. Its
SHA-256 is
`93b134e7961afba3c2eebee2e22d01ef60b36cf388c3c254adec62c0f71981d5`.
The [saved-byte audit](esa-girafe-platform-layout-audit.json) verifies
all three raw range hashes and has SHA-256
`d259645ee75c7cdbfffaaf7731f02d172a3f869a45d3ac1ca2c2070d160f0c8b`.
It reads the three saved ranges and performs no new transfer or model fit.
The raw ranges stay in the local authorized recording directory.
The [portable evidence bundle](esa-girafe-platform-probe-evidence/bundle.zip)
contains the original probe plan, code, terminal result and charge ledger.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_girafe_platform_probe report
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_girafe_platform_probe audit-saved
```
