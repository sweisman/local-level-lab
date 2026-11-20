# The same forecast ranking with three PPP exports

The [saved-only forecast check](ESA_ALTERNATE_PPP_SCORING_PLAN.md) rescored
the two complete ESA 400/120 development settings against three GNSS-only
PPP exports: the original `air1`, plus `mosaic03` and `pwrpak7`. It kept the
original training-selected fit and all **120 identical later epochs** for
every model and export. The `air1` total RMS values exactly reproduce the
sealed original report in all six candidate/settings. Four focused and saved
result tests pass. The complete [machine result](esa-alternate-ppp-scoring-result.json)
contains per-axis errors, source hashes and selected forecast hashes.

| Candidate, profiled processing | `air1` total RMS | `mosaic03` | `pwrpak7` |
|---|---:|---:|---:|
| Globe, specified field | 5.227 m | 5.225 m | 5.225 m |
| Globe, zero field | 2,590.069 m | 2,590.053 m | 2,590.072 m |
| Flat disc, zero field | 3,998.249 m | 3,998.234 m | 3,998.253 m |

The table shows the `increment` IMU-error convention. The separate `point`
convention has the same ordering and differs by less than 0.003 m in these
rounded candidate totals. The preferred specified-field globe passes the
existing descriptive position-accuracy screen against all three PPP exports.
In the original `air1` scores, horizontal RMS is 5.18 m for that globe,
2,589.50 m for the zero-field globe and 3,997.37 m for the disc; height RMS
is 0.71, 54.38 and 83.72 m respectively. The ordering here is driven mainly
by the horizontal trajectory, not by height alone. This still does not
isolate the gyro contribution from the complete IMU/receiver calculation.
The two zero-removal settings remain unresolved because required flat fits
did not pass their original stopping check; they were not rescored into a
decision.

**What this establishes:** the large numerical model separation on this one
opened development flight is not caused by choosing one of these three PPP
exports for the withheld positions. No new fit or native forecast was run,
and the seven reserved ESA flight groups remain closed.

**What it does not establish:** the exports use a shared antenna and a
conventional geodetic coordinate chart. They cannot test common GNSS error
or remove the conditional coordinate-model assumption. The 120-epoch horizon
was selected after earlier development results, and neither aircraft error
law nor a two-stage false-choice rate has been calibrated. These are
numerical preferences on one flight, not an independent scientific detection
or evidence about the cause of the measured angular field.
