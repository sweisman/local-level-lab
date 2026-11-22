# Two more raw GPS records are available for ESA flight 187

The archive contains the raw observations from the Septentrio Mosaic and
NovAtel receivers alongside the original AIR1 record. The first 64 KiB of
each file contains a complete RINEX 3.04 header and consecutive sampled epochs.
Their reported times span the development comparison. This preflight has
not yet checked the comparison epochs themselves.

| Receiver | Original file | Size, bytes | Reported cadence | Carrier observables |
| --- | --- | ---: | ---: | --- |
| Septentrio Mosaic | `lvl0/187/mosaic03/SEPT1870.23O` | 684,326,587 | 5 Hz | Code and phase, including GPS L1/L2 and Galileo E1/E5a/E5b |
| NovAtel PwrPak7 | `lvl0/187/pwrpak7/NMPL20210019C_2023-07-06_19-23-46.23O` | 178,964,794 | 1 Hz | Code, phase and Doppler, including GPS L1/L2 and Galileo E1/E5b |

| Receiver | First and last reported observation times, GPS time, 6 July 2023 | SHA-256 of the first 65,536 bytes |
| --- | --- | --- |
| Septentrio | 10:39:38.6 to 19:33:42.6 | `492bc79b7ac3dde9a03a1901092af72495d61563e77e3a2e4fc842d3de366814` |
| NovAtel | 10:34:38 to 19:24:04 | `486550a522e66fca94fd0233aa8236cfabd2674fd45847c1ff227d776bd473d2` |

Use capped byte ranges, then verify coverage and timing around the same
400 earlier and 120 later GPS reports already used on flight 187. For the
next comparison, use a shared satellite set and common bands before testing
one receiver's additional observations. The raw signal comparison can
separate some receiver-specific effects. The common antenna still leaves
some satellite, propagation and antenna errors shared.
[Original AIR1 window](ESA_RINEX_WINDOW_RESULT.md) ·
[Instrument layout](https://essd.copernicus.org/articles/17/1667/2025/#section2)

The file names and sizes were checked on the authenticated ESA FTPS service.
The bounded transfer checked a pinned, previously verified server certificate.
Both ranges contained exactly 65,536 bytes. No full receiver file or protected
flight was opened during this preflight.
[ESA archive](https://earth.esa.int/eogateway/campaigns/airborne-quantum-gravimetry-airquantumgrav-2023)
