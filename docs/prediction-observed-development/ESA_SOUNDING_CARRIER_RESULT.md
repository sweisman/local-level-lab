# Regional weather moves the carrier paths without changing the shape ranking

Replacing the standard atmosphere with either of two NOAA balloon profiles
moved the GPS and GLONASS carrier paths by up to **6.7 cm horizontally** and
**15.5 cm in height** RMS over the later two minutes. The largest change in
the fixed shape score was **0.0215**. All four replays still favor the globe
over the disc when both predictions use the same zero background field.

| Constellation | Weather profile | Later horizontal RMS shift | Later height RMS shift | Fixed shape score | Change from its standard path |
| --- | --- | ---: | ---: | ---: | ---: |
| GPS | Aasiaat | 2.0 cm | 4.0 cm | −7.126 | +0.0062 |
| GPS | Narsarsuaq | 6.7 cm | 15.5 cm | −7.110 | +0.0215 |
| GLONASS | Aasiaat | 0.22 cm | 1.13 cm | −6.990 | +0.00071 |
| GLONASS | Narsarsuaq | 0.14 cm | 5.33 cm | −6.990 | −0.00009 |

Zero is a tie. RMS shifts are relative to the corresponding standard-atmosphere
carrier path, with the same receiver anchor, satellites, and times. The original
processed export scored −6.923. The balloons were more than 430 km from the
aircraft. These are two measured regional alternatives and give no bound on
aircraft-local delay, antenna error, or coverage on independent flights.

## Saved-path audit

The runner charged all 4,152 steps. Each task saved all 1,038 reconstructed
steps before the runner rejected its result record for a missing required field.
The original run remains terminal with 0/4 passing tasks. A separate audit
checked the saved paths against their sealed hashes, checked the full charges and
matched times, and computed the table from those paths. The adapter now returns
the required field. The numerical run was preserved and the correction has not
been used to rerun it. No inertial fit or reserved flight was used.

## Reproduce the table

With the closed local study, its frozen GPS and GLONASS references and receiver
parent restored, run the report command. It verifies receipts and regenerates
the table's data without replaying any satellite solve.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_sounding_carrier report
```

[Fixed method](ESA_SOUNDING_CARRIER_PLAN.md) ·
[Weather profiles and delay calculation](ESA_SOUNDING_DELAY_RESULT.md) ·
[Saved-path comparisons and runner dispositions](esa-sounding-carrier-result.json)
