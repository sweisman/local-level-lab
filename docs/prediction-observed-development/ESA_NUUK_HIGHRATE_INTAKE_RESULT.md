# One-second GPS from the permanent Nuuk station

The permanent Nuuk receiver, `NUUK00GRL`, matched **all 520 whole-second
aircraft reports** from 11:49:57 to 11:58:36 UTC on 6 July 2023. Every
interval in the two-minute comparison had **at least 11 common GPS
satellites** with continuous carrier observations on both bands. These
counts precede the aircraft score's satellite screens.

The original Dataforsyningen download contains 86,400 epochs. The full
decode and the overlap use GPS time. The intake checks both bands and
carrier lock against the saved half-second records from development
flight 187. It retains the original 520 ground observation blocks and
the station header in a compressed excerpt. [GNET station record](https://go-gnet.org/station-summary/nuuk)

This gives the comparison two nearby ground receivers at one-second
cadence. The [matched range comparison](ESA_NUUK_NEAR_STATIONS_RESULT.md)
uses both receivers on the same satellites and times. The aircraft
error limits remain open.

The original `NUUK00GRL_R_20231870000_01D_01S_MO.crx.gz` is 137,784,570
bytes. The [intake receipt](esa-nuuk-highrate-intake.json) binds its hash,
the converter and the saved aircraft source. The command uses the
same GSI `crx2rnx` 4.2.0 converter as the earlier station checks.
[Converter source](https://terras.gsi.go.jp/ja/crx2rnx.html)

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_nuuk_highrate_intake \
  /path/to/NUUK00GRL_R_20231870000_01D_01S_MO.crx.gz /path/to/crx2rnx
```
