# Averaging a quarter second removes the recorded motion mismatch

On the same 24 October 2009 flight, none of the averaged force directions
required more angular travel than the paired gyro budget. This held with
both averaging widths, both receiver paths, both packet clocks and all
four Earth and field candidates. The [single-packet check](PAIRED_GYRO_INTERVAL_RESULT.md)
had exceeded the budget in 73–78% of the same intervals.

| Force support | Earlier intervals per setting | Later intervals per setting | Intervals exceeding the paired budget |
| --- | ---: | ---: | ---: |
| One packet | 414 | 192 | 303–309 earlier, 149–150 later |
| Quarter second | 414 | 192 | 0 in every setting |
| One second | 414 | 192 | 0 in every setting |

The gyro budget uses the larger recorded angular travel from the two
instruments, with the same timing, frame-rate and gyro count allowances
as before. The result holds using only the acceleration half-count
allowance. Including the additional allowance for orientation change
within the averaging window also produces zero shortfalls.

The measured and predicted force vectors were averaged over the same
whole-packet support. Passing this necessary check means the logged gyro
travel can accommodate the required pairwise turns under the stated
assumptions. It leaves continuous orientation, actual motion within each
packet and instrument calibration open. The four candidates all clear
this check, so it gives no shape decision.

All 64 matched summaries completed, with five focused tests passing and
zero navigation fits. The earlier single-packet result remains available.
[Frozen averaging method](PAIRED_GYRO_AVERAGED_FORCE_PLAN.md) ·
[All summaries and charges](paired-gyro-average-result.json)
