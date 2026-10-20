# Saved-bound unit audit

The six bounds completed, but their comparison adapter checked raw-coordinate coefficients against metre-scaled training coefficients. That is a unit mismatch. The original six failed labels are preserved. This audit converts the saved 27 physical and 24 common-error columns into matching units, with no bound rerun.

| Candidate / removal | Scaled coefficients exactly equal | Largest coefficient difference | N / E / height allowance ratios |
|---|---|---:|---:|
| Globe with specified field / zero | Yes | 0 | 0.982813 / 0.978224 / 0.999978 |
| Globe with specified field / profiled | Yes | 0 | 0.984158 / 0.979309 / 0.999977 |
| Globe with zero field / zero | Yes | 0 | 0.975833 / 0.963066 / 0.999988 |
| Globe with zero field / profiled | Yes | 0 | 0.980135 / 0.969434 / 0.999986 |
| Flat disc / zero | Yes | 0 | 0.999999 / 0.988666 / 0.999999 |
| Flat disc / profiled | Yes | 0 | 0.999995 / 0.991634 / 0.999995 |

The recomputed allowances improve by at most about 3.7%, and height changes by less than 0.003%. This smaller-domain recalculation therefore offers little help with the main vertical uncertainty. It does not establish narrower complete prediction ranges or observational coverage.

| Candidate / removal | Position remainder, height (m) | Included force remainder (m) | Lever remainder (m) |
|---|---:|---:|---:|
| Globe with specified field / zero | 0.12624 | 0.02238 | 0.01493 |
| Globe with specified field / profiled | 0.13494 | 0.02238 | 0.01869 |
| Globe with zero field / zero | 0.08420 | 0.02238 | 0.01119 |
| Globe with zero field / profiled | 0.09999 | 0.02238 | 0.01796 |
| Flat disc / zero | 0.05338 | 0.02238 | 0.00865 |
| Flat disc / profiled | 0.07181 | 0.02238 | 0.01653 |

The force term is included in the position remainder and must not be added again. These are reported bounds, not independent physical error estimates. The remaining position-propagation terms are the next place to inspect; another repetition of the same smaller-domain calculation is not justified.

Any nonzero coefficient difference must be retained or explicitly bounded when constructing a future inequality. The data file reports exact transfer-radius terms; no coefficient is silently replaced here.

[Original comparison](README.md) · [Next step](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
