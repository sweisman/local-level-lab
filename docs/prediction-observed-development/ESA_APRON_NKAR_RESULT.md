# The parked aircraft and Nuuk Museum showed little shared range residual

The parked aircraft and Nuuk Museum matched on **216 satellite range
changes across 18 one-second steps**. Their centered residuals had
correlation **0.014** on that excerpt. Subtracting the museum residuals
raised the RMS from **7.03 mm** for the aircraft alone to **9.46 mm** for
the difference. These results give little evidence that the same
satellite errors dominated both receivers over this short interval.

| Matched one-second residual | RMS |
| --- | ---: |
| Parked aircraft | 7.03 mm |
| Nuuk Museum | 6.43 mm |
| Aircraft minus Nuuk Museum | 9.46 mm |

The comparison used twelve common GPS satellites at every step and the
same final satellite orbits and clocks on both sides. It removed the
receiver clock on the common satellite set. The aircraft residuals
reproduced the earlier fixed-position check before matching. The
original and expanded station files matched the hashes from the
earlier airborne ground-reference study. [Parked aircraft check](ESA_APRON_CARRIER_RESULT.md) ·
[Airborne ground-reference study](ESA_NKAR_GROUND_SCORE_RESULT.md)

These observations come from one short parking interval. Satellite
and time samples share conditions. The comparison cannot attribute
the difference to the aircraft antenna alone or measure the specific
in-flight error direction needed by the forecast. [In-flight accuracy requirements](ESA_CARRIER_ERROR_REQUIREMENTS_RESULT.md)

One task completed all 56 checks and 13 focused software tests
passed. No new flight data was downloaded and no reserved recording
was opened. [Frozen plan](ESA_APRON_NKAR_PLAN.md) ·
[Matched ranges and completion receipt](esa-apron-nkar-result.json) ·
[GSI converter](https://terras.gsi.go.jp/ja/crx2rnx.html)
