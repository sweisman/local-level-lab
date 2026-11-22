# Forecasts across twenty more airborne recording groups

**9/20** groups have later north, east and height errors within the fixed earlier development reference.
**9/20** pass the separate physical prediction screen; 11/20 cannot be scored because the later-cut fit did not pass its numerical check.

| Recording | IMU | Latitude | Duration | Numerical status | Within reference | Physical screen |
|---|---:|---:|---:|---|---|---|
| `7df21c83…` | 21 | 71.9° | 4.07 min | abstain_inner | yes | yes |
| `a953c8dd…` | 21 | -62.3° | 9.08 min | abstain_inner | yes | yes |
| `570b37d2…` | 21 | -58.9° | 7.30 min | abstain_both | — | — |
| `50f24131…` | 21 | -61.2° | 9.23 min | abstain_outer | — | — |
| `74ec8f62…` | 21 | -61.2° | 8.58 min | matched | yes | yes |
| `2791235c…` | 21 | -56.7° | 7.37 min | abstain_both | — | — |
| `f50ff54d…` | 21 | -64.1° | 9.13 min | matched | yes | yes |
| `370cec66…` | 21 | -61.4° | 9.22 min | abstain_both | — | — |
| `48c1bfe2…` | 21 | -61.4° | 7.10 min | abstain_inner | yes | yes |
| `a6e658d1…` | 21 | -61.5° | 9.03 min | matched | yes | yes |
| `2a56eb8f…` | 21 | -62.2° | 9.13 min | abstain_both | — | — |
| `bb8061a4…` | 21 | 72.6° | 6.40 min | matched | yes | yes |
| `5a642167…` | 21 | -61.3° | 9.20 min | matched | yes | yes |
| `c69d0a93…` | 21 | -58.8° | 7.18 min | abstain_outer | — | — |
| `f66ab497…` | 21 | -62.2° | 9.33 min | abstain_inner | yes | yes |
| `8bf60391…` | 21 | -57.1° | 6.28 min | abstain_both | — | — |
| `fd7b81e4…` | 21 | -61.6° | 5.90 min | abstain_outer | — | — |
| `fad74da3…` | 21 | -63.2° | 5.53 min | abstain_outer | — | — |
| `e6629f14…` | 21 | -62.7° | 9.20 min | abstain_both | — | — |
| `dac266ab…` | 21 | -59.1° | 8.88 min | abstain_both | — | — |

These groups were selected without looking at the forecast outcomes,
but they come from the same archive: this is retrospective development,
not independent confirmation. The reference is a fixed earlier error
comparison, not a confidence interval. This study checks one specified
globe-plus-field forecast; it does not compare Earth shapes or calibrate
a detection rule. Overlapping survey flights or installations cannot be
counted as independent replications.

A [GPS-only comparison](REMAINING_GPS_BASELINE_RESULT.md) uses these same
groups and forecast cuts. The IMU forecast had smaller horizontal errors
at all 18 cuts where a passing start was available.

The [saved accuracy audit](ACCURACY_MARGIN_RESULT.md) separately checks
all 80 forecasts, including those whose fits failed to stop. Every one
meets the fixed position-error screen. The nine accepted later-cut groups
and original numerical outcomes stay unchanged.

[Group metadata and forecast errors](remaining-group-summary.csv) · [Detailed forecast errors](remaining-result.csv) · [All numerical starts](remaining-fit-audit.csv) · [Source selection](remaining-groups.csv) · [Frozen method](REMAINING_GROUPS_PREDICTION_PLAN.md) · [Recovery procedure](REMAINING_GROUPS_RECOVERY.md)
