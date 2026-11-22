# Wider arithmetic in complete generated fits

The wider calculation completed all four candidates in **15 of 16** matched
settings, up from **6 of 16** with binary64. It preserved every complete
binary64 setting and passed the [predeclared gate](MATCHED_WIDE_PLAN.md).

| Check | Binary64 | Wider |
|---|---:|---:|
| Fit and forecast technical checks | 64/64 | 64/64 |
| Numerical stopping checks | 47/64 | 63/64 |
| Known-truth stopping and withheld accuracy checks | 16/16 | 16/16 |
| Complete four-candidate settings | 6/16 | 15/16 |

The highest withheld RMS among wider truth-matched fits was 5.75 mm
horizontally and 2.02 mm in height, against a 0.25 m limit per component.
Among the 47 comparisons where both arithmetic versions stopped, the median
of the largest pointwise differences in later positions was 3.26 µm. The
largest difference was 0.192 mm. These forecasts come from four fresh
24-second generated histories.

The single unfinished wider fit used the specified-field globe on a
zero-field globe history, with ±20°/hour offsets and no modeled removal.
It failed the fresh cost-change and stationarity checks. It remains
unfinished under the original stopping rules.

The [per-fit ledger](matched-wide-fits.csv) and [verification
receipt](matched-wide-report.json) retain every result. The verifier checked
the frozen sources and derived wider kernel, regenerated the scoring
coordinates, and replayed the scores from sealed fit and forecast records.
The study charged 3,401 native calls and 138,354,642 packet visits. The
verification started zero fits.

This qualifies the wider solver on the stated generated histories. A
recorded-aircraft comparison still requires matched gyro-free qualification,
receiver uncertainty, and a separate frozen pilot.
