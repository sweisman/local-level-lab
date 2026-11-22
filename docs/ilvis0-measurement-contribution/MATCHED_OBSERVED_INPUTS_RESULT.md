# Matched aircraft inputs are ready for the numerical preflight

Both original files passed the recorded packet and installation
checks. All **1,111 common receiver epochs** fit inside both clock
conventions, including the full ±0.15-second timing allowance.

| Recording | Original IMU packets | Training receiver epochs | Later receiver epochs | Smallest remaining timing margin across both clocks |
|---|---:|---:|---:|---:|
| IMU8 | 133,680 | 445 | 223 | 0.400 s |
| IMU21 | 88,478 | 295 | 148 | 0.041 s |

The two clocks use different packet counts for the training prefix.
The prepared inputs retain each packet offset, the original signed
increments, the elapsed header interval and the physically converted
increments. The three GPS streams share exact epoch tags on the
prepared input. Each recording's later coordinates are in a separate
scoring artifact. The fitter receives only its earlier GPS coordinates,
and the forecast can use later IMU packets and GPS query times.

The [input receipt](matched-observed-inputs-receipt.json) binds every
artifact to its original file and the [preparation freeze](matched-observed-inputs-freeze.json).
All 27 focused tests passed. Input preparation ran zero fits.

The [eight-case numerical preflight](MATCHED_OBSERVED_NUMERICAL_PLAN.md)
sets the next scope. It checks that the recorded input reaches all four
models, and that forecasting reproduces the fitted prefix before
opening the scoring positions.
