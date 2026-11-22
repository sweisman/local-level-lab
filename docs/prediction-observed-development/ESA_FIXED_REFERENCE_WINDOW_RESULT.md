# Reykjavík station data overlap the second ESA ground stop

The fixed `REYK00ISL` receiver was **0.93 km** from the centre of the
previously selected Reykjavík ground stop in ESA recording 187. Its
archived observations overlap **61 consecutive 30-second times** from
16:52:12 to 17:22:12 UTC on 6 July 2023. Each has both code and carrier
observations on the two selected GPS signals for at least 11 satellites.
[IGS station metadata](https://network.igs.org/REYK00ISL) ·
[BKG observation file](https://igs.bkg.bund.de/root_ftp/IGS/obs/2023/187/REYK00ISL_R_20231870000_01D_30S_MO.crx.gz)

This provides a nearby reference for checking GPS errors shared by the
receivers during that stop. The aircraft antenna coordinates still need
to be compared with those of the fixed station, using common satellites
and the unrounded GPS times. This result establishes ground-station
availability. No aircraft-side raw epochs have been matched yet.
[Frozen aircraft stop](SECOND_GROUND_INTERVAL_RESULT.md)

For the earlier airborne comparison in Greenland, the closest active
stations identified were `NUUK` and `KAPI`, 34–41 km and 43–51 km away
during the later two minutes. `KSUT` opened after the flight. The checked
EPOS date queries returned no 6 July observations for the nearby stations.
The Danish archive describes a separate sign-in route. Coverage for those
stations remains unresolved. The Reykjavík data apply to the later ground
stop. [GNET coordinates](https://go-gnet.org/gnet-coordinates) ·
[KSUT installation](https://go-gnet.org/station-summary/ksut) ·
[EPOS data lookup](https://gnss-epos.eu/glass-api/glass-api-section-t2-rinex-file-metadata/) ·
[Danish archive access](https://go-gnet.org/data-and-site-log)

## Reproduce the station excerpt

The original 4.15 MB observation day is retained under
`data/esa-fixed-reference-inputs`. The excerpt preserves the original RINEX
header and all 61 selected records. The report records the original file,
converter source and expanded data hashes. Build `crx2rnx` from the 4.2.0
GSI source archive, then run the command below with its executable path.
[Converter and license](https://terras.gsi.go.jp/ja/crx2rnx.html) ·
[Selected observations](esa-fixed-reference-reyk.rnx.gz) ·
[Provenance and checksums](esa-fixed-reference-window-result.json)

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_fixed_reference_window \
  data/esa-fixed-reference-inputs/REYK00ISL_R_20231870000_01D_30S_MO.crx.gz \
  /path/to/crx2rnx
```
