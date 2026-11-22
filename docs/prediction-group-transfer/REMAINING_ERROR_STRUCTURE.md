# Error patterns in saved aircraft forecasts

Nine of twenty selected recording groups have a usable later-cut forecast. The other eleven remain in the denominator as unscorable numerical outcomes. This audit uses the saved forecast errors only; it makes no new fit or model comparison.

| Later-position error | North | East | Height |
|---|---:|---:|---:|
| Median RMS across nine groups | 1.04 m | 0.69 m | 4.43 m |
| Median absolute trend | 0.95 m/min | 0.64 m/min | 2.97 m/min |
| Median adjacent-epoch correlation | 0.9999 | 0.9999 | 1.0000 |

A trend is a linear summary of each forecast error, not an independent estimate of sensor drift. The CSV also records signed means, final errors and adjacent-epoch correlations for each group. These correlations include slow trends, so they do not measure a stationary noise process.

All nine scored groups passed the fixed development reference and separate physical screen in the [parent report](REMAINING_GROUPS_PREDICTION_RESULT.md). Eleven could not be scored. This selected, same-archive sample does not calibrate uncertainty, establish prediction coverage or support a scientific detection.

[Per-group saved error audit](remaining-error-structure.csv) · [Parent forecast method](REMAINING_GROUPS_PREDICTION_PLAN.md)

The [earlier-to-later drift check](ERROR_TRANSFER_RESULT.md) tests whether
the error pattern carries across two adjacent periods. Height improved in
15 of 20 diagnostic groups. Horizontal error improved in only three.
