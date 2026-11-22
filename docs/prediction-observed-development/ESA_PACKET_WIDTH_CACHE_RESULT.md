# Reusing exact widths does not reliably speed up both packet bounds

All four calculations reproduced the archived bound files byte for byte
and kept the same packet-work counts. The speed comparison missed its
predeclared gate.

| 470-packet prefix | Archived bound CPU | Cache bound CPU | Archived / cache |
| --- | ---: | ---: | ---: |
| Zero-field globe | 26.59 s | 24.71 s | 1.076× |
| Zero-field disc | 24.78 s | 25.07 s | 0.988× |

The median ratio was 1.032×. The gate required a median greater than 1.05×
and a ratio of at least 1 on both prefixes. These are two order-balanced
measurements, so they do not establish a repeatable speed gain. The original
calculation stays in use.

The study finished both matched tasks in 65.2 seconds with four bound
charges. Ten local checks passed. The revised source, exact-match results
and timing failure are preserved with the frozen inputs.

- [Frozen comparison](ESA_PACKET_WIDTH_CACHE_PLAN.md)
- [Timing results and hashes](esa-packet-width-cache-result.json)
- [Verified evidence and archived candidate](esa-packet-width-cache-evidence/README.md)
