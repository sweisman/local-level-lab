# Same-day weather changes the estimated GPS signal delay

Weather-balloon observations from Aasiaat and Narsarsuaq both increase the
estimated neutral-atmosphere delay compared with the standard atmosphere.
At the aircraft's reported height, the change for a signal coming from
directly overhead is **1.7–6.3 cm** over the later two minutes.

| NOAA sounding | Distance to track | Overhead delay above standard, later two minutes | Largest change since the last training report |
| --- | ---: | ---: | ---: |
| Aasiaat | 514–519 km | 1.7–2.5 cm | 8.2 mm |
| Narsarsuaq | 433–452 km | 6.3 cm | 0.9 mm |

The flight's 520 reports cover about nine minutes. Reported ellipsoid
heights range from 1,483 to 3,238 m. Both soundings are nominally 12 UTC on
6 July 2023. They were launched at 11:03 and 11:10, respectively. Shifting
the altitude used in each sounding by ±50 m changes the later absolute
delay range to 0.5–7.4 cm across the six scenarios. The largest change
relative to the last training report is 8.8 mm across those scenarios.

These are signal-delay changes for an overhead satellite. Low-elevation
signals pass through more atmosphere, and different satellite directions
can turn that range error into different position errors. The soundings
were several hundred kilometres away, so the values describe sensitivity
to observed regional weather. They do not bound local weather or certify
aircraft position. Quantifying the effect on the shape comparison requires
replaying the GPS and GLONASS paths with the alternate delay models. No
inertial fit or reserved flight was used.

## Reproduce the calculation

The [source catalog](esa-sounding-sources.json) has the NOAA archive URLs
and SHA-256 hashes. The saved excerpts contain the complete header and
declared level records for each selected sounding. NOAA updates the station
archives in place, so use the saved excerpts to repeat these exact results.
[Aasiaat excerpt](esa-sounding-GLM00004220.txt) ·
[Narsarsuaq excerpt](esa-sounding-GLM00004270.txt)

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_sounding_delay
```

[Fixed method](ESA_SOUNDING_DELAY_PLAN.md) ·
[All altitude scenarios and source hashes](esa-sounding-delay-result.json)
