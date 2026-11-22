# The permanent Nuuk receiver matches 17 aircraft observation times

The SONEL archive has raw observations from `NUUK00GRL` on 6 July 2023.
All **17** ground times in the selected aircraft window match exactly.
Each pair has **12 GPS satellites** with both code and carrier phase on
the required frequencies. The selected records span 11:50:12–11:58:12 UTC.
[SONEL data access](https://www.sonel.org/Data-access) ·
[Station record](https://go-gnet.org/station-summary/nuuk)

Four ground epochs fall inside the two-minute test of the constructed
displacement. Eleven satellites have both frequencies throughout the
three intervening 30-second periods, with complete half-second aircraft
samples and no reported lock flags on those arcs. These epochs cover
90 seconds. The ground cadence limits what they can show about changes
within each interval. The separate 1 Hz Nuuk Museum file would provide
finer time coverage. [Nuuk Museum catalogue](ESA_GROUND_REFERENCE_AVAILABILITY.md)

The original 5,759,997-byte compressed day and the selected observations
were retained with their hashes. Station coordinates from the observation
header are approximate. The intake made no new fits and opened no reserved
recordings. Eleven focused software tests passed.
[Frozen intake plan](ESA_NUUK_GROUND_INTAKE_PLAN.md) ·
[Coverage, source and checksums](esa-nuuk-ground-intake.json) ·
[Selected ground observations](esa-nuuk-ground-window.rnx.gz)

To reproduce from the [original SONEL file](ftp://ftp.sonel.org/gps/data/2023/187/NUUK00GRL_R_20231870000_01D_30S_MO.crx.gz),
build `crx2rnx` from the verified GSI 4.2.0 source and run the intake from
the repository root with the saved development carrier study available.
[GSI converter and license](https://terras.gsi.go.jp/ja/crx2rnx.html)

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  ~/venv/bin/python -m lll.esa_nuuk_ground_intake \
  /path/to/NUUK00GRL_R_20231870000_01D_30S_MO.crx.gz /path/to/crx2rnx
```
