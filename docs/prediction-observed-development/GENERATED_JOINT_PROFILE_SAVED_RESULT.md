# Joint-path profile: saved generated-case audit

The [read-only audit](generated-joint-saved-audit.json) verifies all three
profiles from the sealed generated `straight-level` case. It rechecks the
source and replay completion hashes, the exact three forecast-replay
artifacts, the construction journal hash chain, native prepayment, saved
linear profiles and native nonlinear comparisons. It makes no new fit or
native calculation.

Both replay studies closed **terminally**, so their task gates remain failed.
The first stopped at a native normalized-bound check. In the second, the
largest boundary correction was only `2.22e-16`, and all three nonlinear
checks finished. Its final receipt check failed because it expected 119
newly generated later positions. This replay instead read those already
sealed positions. The audit finds exactly 119 fewer `generated_samples` charges
and exact agreement on the other two construction resources. The failure
and the original prepaid charges are retained.

| Candidate | Linear future cost | Nuisance rank | Parameters at bounds | Native minus tangent RMS, N/E/U |
|---|---:|---:|---:|---:|
| Globe, specified field | 0.1561 | 26/26 | 6 | 5.48 / 4.01 / 20.46 m |
| Globe, zero field | 0.4077 | 26/26 | 8 | 27.53 / 5.11 / 1.78 m |
| Flat disc, zero field | 0.1481 | 26/26 | 4 | 13.67 / 15.07 / 6.61 m |

Every profiled correction reaches a normalized magnitude of 2, moving some
calibrations from one permitted bound to the opposite bound. The nonlinear
paths then differ from their local tangent predictions by metres to tens of
metres. **The linear costs cannot rank the physical models.** The slightly
smaller flat linear cost is an unreliable extrapolation, not a flat preference;
the generated truth in this case is the specified-field globe. This test
shows why a local joint profile is unsafe when unconstrained calibration
moves across its full allowed range.

Next, restrict a profile to a prospectively chosen local trust region or use
a fully nonlinear bounded compatibility calculation, with a separate finite
study and known-answer checks. Neither would replace earlier-only held-out
prediction. Real-aircraft receiver and IMU error laws, absolute adequacy and
null calibration remain open; no scientific decision is made here.
A [separate radius-0.1 control](GENERATED_LOCAL_PROFILE_RESULT.md) has now
completed. Its local tangent still differs from the nonlinear path by up to
about 1.3 m RMS on an axis, so it does not qualify this statistic for model
selection.
