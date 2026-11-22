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

A saved-derivative check narrows the numerical issue. At each final fitted
point, a bounded linear correction predicts a cost reduction of about
3.107×10⁻⁶ from a cost near 10,428. Computing that reduction directly and
as −2*r·(Jd)−|Jd|² agrees within 0.0001% in all four cases. The last
attempted full correction instead **increased** the actual cost by about
1.86–1.88×10⁻⁵, and the solver rejected it. Thus, rounding in the
predicted-cost subtraction does not explain the failed full step. The
remaining issue is the local model's accuracy along that correction, or how
the trust step moves through the curved, bounded fit. This is a diagnostic
from the sealed residuals, Jacobians and step histories; it makes no new fit.
The [saved-only report](ESA_400_120_STOPPING_GEOMETRY.json) records each
fit-artifact hash, both reduction calculations and the original failed label.
It can be regenerated with
`PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_matrix_stopping_geometry --root .`.

Any later attempt to recover these settings needs a **separate**, source-bound
solver qualification that tests curved bounded valleys against known answers,
with the same scientific
inputs and physical bounds. It must preserve the four original failures,
charge new work separately, and apply the same numerical acceptance rule to
all three physical models. A looser stopping rule cannot be inferred from
the close agreement of these starts.

A [generated known-optimum check](../prediction-group-transfer/CURVED_BOUNDED_SOLVER_RESULT.md)
passed all eight cases with both the existing trust region and a centered
objective solver. SciPy TRF reached nearly exact costs yet failed the
unchanged position check on six curved cases. Flight-scale qualification
remains open before any newly frozen observed comparison.

[Full matrix result](ESA_400_120_MODEL_MATRIX_RESULT.md) ·
[Every fit](ESA_400_120_MODEL_MATRIX_FITS.csv) ·
[Frozen plan](ESA_400_120_MODEL_MATRIX_PLAN.md).
