# The ground force lag transfers imperfectly to flight

The best common shift on the three Greenland ground clips was **100 ms
earlier**. Their individual peaks stayed within 10 ms of that shift at all
four averaging widths. In flight, the first and last clips favored
different shifts. The middle clip's best correlation across all tested
lags and widths was **0.40**, rounded to two decimal places.

| Clip | Best shift with 0.1 s averaging | With 0.3 s | With 1.1 s | With 2.1 s | Correlation at common shift, 1.1 s | Peak correlation, 1.1 s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ground 1 | −110 ms | −110 ms | −110 ms | −110 ms | 0.953 | 0.958 |
| Ground 2 | −110 ms | −110 ms | −110 ms | −110 ms | 0.968 | 0.978 |
| Ground 3 | −100 ms | −90 ms | −100 ms | −100 ms | 0.973 | 0.973 |
| Airborne 1 | −70 ms | −70 ms | −80 ms | −80 ms | 0.968 | 0.979 |
| Airborne 2 | −1,920 ms | −1,800 ms | −1,920 ms | −1,920 ms | 0.108 | 0.354 |
| Airborne 3 | +10 ms | +60 ms | +60 ms | +10 ms | 0.850 | 0.981 |

The [fixed check](ESA_GIRAFE_FINE_LAG_PLAN.md) chose the common shift by
maximizing the weakest ground match at 1.1 seconds. Applying it unchanged
to the air clips still clears the 0.70 correlation reference on two of
three. The weak middle clip's maximum is too small to interpret as a time
measurement. On all three airborne clips, even the best correlations at
the shortest averaging width stay below 0.70.

The observations support a repeatable relative shift on this ground stop.
Sensor response, motion and recorder timing can all affect the airborne
matches. The first and last airborne peaks differ by 140 ms at 1.1 seconds.
That spread leaves fine airborne alignment unqualified for a separate
angular prediction check. The original timing and rate-mapping verdicts
remain in their own reports.

The six original clips and matched iMAR supports yielded **9,624 scores**.
All 246 prior coarse-grid correlations reproduced within `4.85e-10`.
There were zero new source transfers, model fits or reserved-flight reads.
The [summary receipt](esa-girafe-fine-lag-result.json) ties the results to
their fixed inputs. The full grid is in the evidence bundle.

[Source and execution receipts](girafe-fine-lag-evidence/README.md) ·
[Verified reproduction bundle](girafe-fine-lag-evidence/bundle.zip)
