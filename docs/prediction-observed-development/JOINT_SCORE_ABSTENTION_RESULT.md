# The provisional decision rule abstains on the ESA flight

In both complete settings on ESA recording 187, only the specified-field
globe stayed compatible. Its joint errors were much smaller than the assumed
uncertainty scale predicts, so the absolute adequacy check withheld a shape
decision. Two other settings remain incomplete because of the original
flat-disc stopping failures. The relative ranking still favors the
specified-field globe.

| Saved cases | Shape calls | Shape abstentions | Incorrect shape calls |
|---|---:|---:|---:|
| Twelve generating-model development histories | 6 | 6 | 0 |
| Two separate generated route controls | 0 | 2 | 0 |
| Four ESA settings on one development flight | 0 | 4 | No known label |

Two of the six shape calls in the first group also correctly identified
zero background field. Four cases in that group left both shapes compatible
and two left every candidate above the upper limit. The straight and turning
controls use the same seed and both leave all candidates compatible. They
test the effect of route shape on the rule and cannot establish error rates.

The rule uses a central chi-square reference for a fixed Gaussian forecast.
It retains low-error candidates as plausible while requiring adequacy before
issuing a decision. The replay neither calibrates the reference for fitted
aircraft models nor establishes whether the low ESA errors reflect the
receiver scale, missing correlation structure or some other factor.

The replay reused the previous scores and reproduced both route controls
under the predeclared bounds. It made no new fit and reproduced its receipt
byte for byte. The 53-stretch baseline and seven closed ESA groups were not
used by this check.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.joint_score_abstention replay
```

[Fixed rule](JOINT_SCORE_ABSTENTION_PLAN.md) · [Frozen inputs](joint-score-abstention-freeze.json) ·
[All dispositions](joint-score-abstention-result.json)
