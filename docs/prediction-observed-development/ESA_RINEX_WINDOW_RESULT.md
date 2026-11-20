# Raw GPS observations matched to an ESA forecast window

A verified excerpt of the original AIR1 receiver file covers the full
400/120 development comparison on ESA recording 187. It contains **1,041
consecutive half-second records**. Every record contains L1 and L2 code
and carrier phase from **11–12 GPS satellites**. The file also carries
GLONASS observations. All 520 existing query times match distinct raw
records within **0.50 milliseconds** in GPS time.

| Item | Verified value |
| --- | --- |
| Receiver file | `air10706a.23o`, RINEX 3.04 |
| Raw record range | GPS week 2269, seconds 388214.5–388734.5 |
| Original file size | 363,446,705 bytes |
| Retained header and records | 5,783,246 bytes before compression |
| Access | Explicit FTP restart offsets, authenticated transport, matching overlaps |

The first offset request returned the file prefix. A later attempt
returned the requested data but timed out on its final control reply.
The successful method checked the restart reply, read each capped byte
span and verified the overlaps. It reproduced that earlier complete
range byte for byte. The original header and all retained satellite
records are unchanged. The header still describes the full source file.
[Transfer correction](ESA_RINEX_BOUNDED_STREAM_PLAN.md)

The matching broadcast navigation, final GPS orbit and final GPS clock
products were downloaded from the German Federal Agency for Cartography
and Geodesy archive. Their exact URLs and hashes are recorded. A
receiver-only position solve has yet to be run. A later comparison can
test processing differences against the existing receiver export. Both
solutions would share the aircraft antenna and the satellite observations.
The seven reserved ESA groups remained closed.
[Product files and hashes](esa-rinex-products.json) ·
[IGS final orbit and clock products](https://igs.org/products/)

To reproduce the excerpt, use the approved ESA FTPS certificate and
account credentials in `~/.esa-ftps.netrc` with permission mode 600.
Run from the repository root. The command checks each byte-range hash
and the final uncompressed excerpt hash.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_rinex_replay \
  --certificate /path/to/esa-ftps-peer.pem --output air10706a-400-120.23o
```

To check an existing acquisition without network access, replace the
`--certificate` option with `--cache` and the directory holding its
verified byte ranges.

[Original window plan](ESA_RINEX_WINDOW_PLAN.md) ·
[Range hashes and timing checks](esa-rinex-window.json) ·
[Existing forecast window](ESA_400_120_MODEL_MATRIX_PLAN.md)
