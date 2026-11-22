# Which satellite corrections can be tested on the ESA development flight?

The final satellite orbit file covers all **12,354 satellite observations**
used in the saved GPS code solution. The final 30-second clock file omits
GPS satellite G17, which was used at all **1,041 epochs**. The remaining
**10–11 satellites per epoch** have both products. This is a coverage check.
No receiver positions were recomputed and no flight models were fitted.

| Candidate comparison | What the saved products support |
| --- | --- |
| Broadcast versus final orbits | Keep every satellite. Use the same broadcast clocks and code measurements on both sides. |
| Broadcast versus final orbits and clocks | Use a separately declared common satellite set on both sides. Dropping G17 only on one side would mix a product change with a change in satellite geometry. |

The coverage audit checks the hash of each archived product and the sealed
dual-frequency position rows. It checks the listed GPS satellites at
each 0.5-second report from 11:49:56.5 to 11:58:36.5 UTC on 6 July 2023.
It requires both clock samples bracketing a window that starts 0.2 seconds
before the reported time, when the satellite signal could have been sent.
It also requires three extra 15-minute orbit samples on each side of that
window's orbit bracket. This verifies the interpolation inputs. The orbit
interpolation and the treatment of code biases for final clocks need their
own checks before a comparison. Only recording 187 was used.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_precise_gps_support
```

[Product URLs and hashes](esa-rinex-products.json) ·
[Saved GPS solution](ESA_RINEX_CODE_RESULT.md)

## Ground references

The campaign team reports placing a Javad receiver at the airport when
possible. The authenticated ESA Level 0 listing for 187 shows aircraft
instrument folders `air1`, `girafe`, `mosaic03`, `pwrpak7` and `rqh01`,
with no separate base folder. The listed contents of `air1` contain
only the aircraft RINEX record. Availability of the campaign's base
observations during this window remains unverified.
[Campaign instrumentation](https://essd.copernicus.org/articles/17/1667/2025/#section2) ·
[Aircraft-file receipt](ESA_RINEX_WINDOW_RESULT.md)

The permanent Nuuk station, `NUUK00GRL`, is 13.2–41.3 km from the
development track using a spherical horizontal distance. The checked EPOS
query returned no daily file for 6 July. Kangerlussuaq's `KELY00GRL`
has catalog entries for 5 and 7 July on that query, with none for the
target day. The KELY equipment log records an elevation-mask change on
6 July, which does not establish why the file is missing from that
catalog. The GNET operator's distribution uses a sign-in. No matching
ground observation file was acquired.
[Nuuk station and access links](https://go-gnet.org/station-summary/nuuk) ·
[Official Nuuk coordinates](https://go-gnet.org/gnet-coordinates) ·
[KELY equipment history](https://network.igs.org/KELY00GRL)

A surveyed ground receiver could check part of the shared satellite and
propagation errors. An orbital replay likewise tests a specific shared
input. Calibration of absolute aircraft accuracy still needs limits on
aircraft-specific effects such as antenna multipath and receiver tracking.
