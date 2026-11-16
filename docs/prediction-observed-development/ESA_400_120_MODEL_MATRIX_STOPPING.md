# Why two ESA settings abstain

The four zero-removal flat-disc fits all stopped after 43–45 evaluations,
well below the frozen 200-evaluation ceiling. Each reports **“no positive
predicted decrease”** and fails the unchanged fresh-position stability check.
The two fixed starts and two IMU error conventions reached nearly the same
training cost, but agreement between starts is not the declared convergence
test.

| Error convention | Start | Evaluations | Fresh north-position RMS change | Frozen RMS limit |
|---|---:|---:|---:|---:|
| Increment | 0 | 45 | 1.5032 mm | 1.0000 mm |
| Increment | 1 | 45 | 1.5032 mm | 1.0000 mm |
| Point | 0 | 43 | 1.5032 mm | 1.0000 mm |
| Point | 1 | 43 | 1.5032 mm | 1.0000 mm |

The saved fresh stationarity values are about 1.82×10⁻⁶, below the
declared 10⁻⁴ stationarity limit. The failed position check is therefore
specific and reproducible; simply granting more evaluations would not
address the reported stopping reason. The original four outcomes remain
nonpassing, and both zero-removal matched settings remain unresolved.

Any later attempt to recover these settings needs a **separate**, source-bound
solver qualification with known-answer controls and the same scientific
inputs and physical bounds. It must preserve the four original failures,
charge new work separately, and apply the same numerical acceptance rule to
all three physical models. A looser stopping rule cannot be inferred from
the close agreement of these starts.

[Full matrix result](ESA_400_120_MODEL_MATRIX_RESULT.md) ·
[Every fit](ESA_400_120_MODEL_MATRIX_FITS.csv) ·
[Frozen plan](ESA_400_120_MODEL_MATRIX_PLAN.md).
