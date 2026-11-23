# Aircraft antenna records on ESA flight 187

None of the three receiver files identifies the shared aircraft antenna.
The Septentrio header says `Unknown`. The NovAtel and primary Javad headers
leave the antenna type blank. The campaign paper confirms that all three
receivers share one roof antenna. Their agreement can check receiver
tracking, but any error introduced at the antenna can affect all three.
[Campaign instrumentation](https://essd.copernicus.org/articles/17/1667/2025/#section2)

## Scope

Read at most 16,384 bytes from the start of each of two files on the
already-open development flight. Use the authenticated ESA archive with
certificate verification. Stop parsing at the RINEX end-of-header record.
Record the hash of the exact header bytes, receiver and antenna model fields,
antenna offsets and any phase-centre correction declarations. Omit serial
numbers. A model name identifies a usable calibration only if it can be
matched to a calibration record and tied to the antenna used by the primary
receiver. No trajectory observations, new model fits or reserved flights
enter this inventory.

| Archive path | Maximum first-byte read |
| --- | ---: |
| `/lvl0/187/mosaic03/SEPT1870.23O` | 16,384 bytes |
| `/lvl0/187/pwrpak7/NMPL20210019C_2023-07-06_19-23-46.23O` | 16,384 bytes |

## Evidence

| Receiver field | Antenna field | Header bytes | Header SHA-256 |
| --- | --- | ---: | --- |
| SEPT MOSAIC-X5, 4.12.1 | `Unknown` | 3,362 | `9416cda1c1b70bdb56ecd8d3cb7f6fe33cde6fe5a3a172901b59a342d40ae0b8` |
| NovAtel GPSCard | Blank | 4,346 | `7c259eb3e173b635bfe82ed00581ffc552d1ce5b58d4252c9bf0131fc613cd9c` |

Both files declare RINEX 3.04 mixed observations. Both report zero offsets
from the marker to the antenna reference point in height, east and north.
Neither declares that antenna phase-centre corrections were applied. The
zero offsets and missing declarations leave the actual antenna calibration
and installation corrections unknown. [RINEX 3.04 format](https://files.igs.org/pub/data/format/rinex304.pdf)

Each fresh header matches the copy already sealed in the three-receiver
study. To reproduce the hashes, open `inputs/0005.rnx.gz` and
`inputs/0006.rnx.gz` inside the bundle, decompress each, and hash through
the line ending of `END OF HEADER` in columns 61–80. The check used two
capped reads and no model fits. [Three-receiver comparison](ESA_PARALLEL_RAW_RECEIVER_RESULT.md) ·
[Sealed bundle](esa-parallel-raw-receiver-evidence/bundle.zip)
