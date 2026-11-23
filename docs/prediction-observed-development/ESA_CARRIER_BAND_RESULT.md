# The two GPS bands show different changes in the air and on the ground

On ESA development flight 187, the recorded two-band correction moved
the fixed carrier score by **−4.75% of the saved comparison gap**. The
same calculation on the distant Qaqortoq receiver gave **+1.58%**.
These percentages describe the change from using the L1 carrier alone
to using both GPS bands on the already matched portion of the score.

| Correction on the same 1,236 satellite–interval pairs | RMS | Signed share of score gap |
| --- | ---: | ---: |
| Aircraft | 5.21 mm | −4.75% |
| Qaqortoq | 3.45 mm | +1.58% |
| Aircraft minus Qaqortoq | 5.87 mm | −6.33% |

All 120 one-second intervals reproduced, including the aircraft's
intermediate half-second lock checks. The correlation of the paired
band corrections was 0.11. On this flight, the distant station's band
correction is therefore a poor substitute for the one measured on the
aircraft. The band difference includes receiver noise and other
frequency-dependent effects alongside changing ionospheric delay.
[GPS carrier combinations](https://gssc.esa.int/navipedia/index.php/Combination_of_GNSS_Measurements)

The archived carrier reconstruction already used both bands. The
projection measures the correction it applied. Errors common to the
two frequencies, absolute GPS accuracy and transfer to independent
flights remain open. No new path or Earth-model fit was calculated.
Five focused tests passed. No reserved observations were opened.

[Frozen plan and replay commands](ESA_CARRIER_BAND_PLAN.md) ·
[Original matched carrier score](ESA_QAQ_GROUND_SCORE_RESULT.md) ·
[Source bindings](esa-carrier-band-freeze.json) ·
[Results by interval](esa-carrier-band-result.json).
