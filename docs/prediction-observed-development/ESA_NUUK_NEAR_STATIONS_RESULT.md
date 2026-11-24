# How closely do the two Nuuk stations agree?

The two stations, about 1 km apart, differed by **6.49 mm RMS** in
one-second GPS carrier-range changes after removal of each receiver's
clock change. All 120 intervals were present in the source records.
The carrier-quality checks and common-satellite requirement retained
**100 intervals and 994 satellite range changes**.

| Ground station pair | RMS difference on the same 994 range changes |
| --- | ---: |
| Nuuk Museum and permanent Nuuk | 6.49 mm |
| Nuuk Museum and Qaqortoq | 7.24 mm |
| Permanent Nuuk and Qaqortoq | 3.77 mm |

All three comparisons used identical times, satellites, orbit and clock
products, and the same atmospheric model. Permanent Nuuk agreed more
closely with distant Qaqortoq than with Nuuk Museum on these rows. The
pairwise differences leave the error of each individual station unknown.

## Effect on the saved model score

The Nuuk Museum residuals project to −2.42% of the saved score gap, and
permanent Nuuk projects to +3.09%, on the common satellite rows. If both
stations observe the same shared range error, hiding an error that shifts
the score by the full gap would require at least one station to have
**5.78 mm RMS** of local residual error. The observed difference requires
**3.25 mm RMS** at one station even when the score shift is unrestricted.
These are lower bounds under the shared-error assumption. The measurements
leave upper bounds on station error and aircraft-specific error open.

One task completed all 124 charged checks. No aircraft fits ran, and no
reserved flights were used. [Fixed plan](ESA_NUUK_NEAR_STATIONS_PLAN.md) ·
[Range rows and checked bounds](esa-nuuk-near-stations-result.json) ·
[Source intake](ESA_NUUK_HIGHRATE_INTAKE_RESULT.md)

Use the sealed run to regenerate the result from the repository root.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_nuuk_near_stations report
```
