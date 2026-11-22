# Compare both solvers on the new ESA window

Use the [prepared input](OBSERVED_DISPATCH_INPUT_PLAN.md) from ESA
development recording 187. Fit both globe models with both upstream
processing assumptions, both GPS error policies and starts 0 and 1.
Each of the 16 tasks runs the wide and selective tangent on identical
training positions, inertial increments and forecast times.

Keep the earlier method's physical bounds and 200 evaluations per fit.
Require both methods to converge and retain every fitted parameter.
Compare their predicted positions with a 1 cm maximum separation.
Then check both starts together. Same-start costs must agree within
`1e-8` of their larger cost, with no absolute allowance. If the preferred
starts differ, each must be near the other's minimum and the paths from
all near-minimum starts must agree within 1 cm. Leave the existing flat
calculation on the wide method.

This checks numerical substitution. A test of aircraft prediction
accuracy requires later measured positions and its own evidence. The
paired workers receive 800 earlier GPS positions and 400 later times.
All 16 paired outcomes, including failures, are required for release.

The original allowance uses four one-thread workers, a 30-hour wall
limit and at most 402 native calls per pair. The packet-visit limit uses
the verified training and forecast lengths. Keep the
[earlier recovery limits](OBSERVED_DISPATCH_RECOVERY.md) under the new
study identity. Preserve sealed failures and resume only unfinished
technical work under the qualified shared recovery procedure.

Once the input preparation closes, `lll.esa_dispatch_pairs prepare`
checks its manifest and the saved generated and software qualifications
before creating `data/esa-dispatch-fresh-pairs-v1`. Preparation does not
start fits or open original aircraft files.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_dispatch_pairs request
env PYTHONPATH=analysis PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ~/venv/bin/python -m pytest -q \
  analysis/tests/test_esa_dispatch_pairs.py analysis/tests/test_esa_dispatch_pair_report.py \
  --junitxml=docs/mixed-tangent-hybrid/observed-dispatch-fresh-tests.xml
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_dispatch_pairs prepare
```

After the run closes, use `lll.esa_dispatch_pair_report` through the
numerical guard with `--manifest-sha256` from preparation. The verifier
checks the original completion and any qualified recovery stage, then
reports all 16 terminal pairs and all eight start comparisons.
