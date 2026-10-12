# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit completed saved records only; never decode, integrate, or refit originals."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import statistics

from lll import ilvis0_recovery_diagnosis as diagnosis

ROOT = Path(__file__).resolve().parents[2]
GUIDE = Path(__file__).resolve().parent
RUNTIME = ROOT/'data/ilvis0-convergence-recovery-trial-20261012'


def main():
    summary, hashes = diagnosis.load_completed(RUNTIME)
    rows = [diagnosis.inspect_fit(k, v) for k, v in sorted(summary['results'].items())]
    categories = collections.Counter(r['failure_class'] for r in rows)
    counts = {role: dict(total=sum(r['role'] == role for r in rows),
                        passed=sum(r['role'] == role and r['converged'] for r in rows))
              for role in sorted({r['role'] for r in rows})}
    control = '570b37d23af5e245dd461051'
    control_rows = [r for r in rows if r['segment_id'] == control]
    failed = [r for r in rows if not r['converged']]
    result = dict(version=diagnosis.VERSION, starts=summary['starts'],
                  native_sweeps=summary['native_sweeps'], counts=dict(categories), roles=counts,
                  control_passed=sum(r['converged'] for r in control_rows),
                  control_total=len(control_rows),
                  recovered_primary_fits=sum(r['converged'] and r['role'] == 'primary'
                                            and r['segment_id'] != control for r in rows),
                  median_failed_condition=statistics.median(r['jacobian_condition_ratio'] for r in failed),
                  qualification=summary['qualification'], fits=rows,
                  observed_fit_starts=0, native_predictions=0, original_labels_changed=False,
                  scientific_decision='abstain')
    (GUIDE/'diagnosis.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    with (GUIDE/'fits.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    table = '\n'.join(f"| {r['segment_id'][:8]} | {r['case_id'].removeprefix('bias1_')} | "
                      f"{r['model']} / {r['role']} | {r['evaluations']} | "
                      f"{r['stationarity_ratio']:.4g} | {r['probe_reason']} |" for r in failed)
    text = f'''# Recovery stopping diagnosis

The trial is complete: **15 of 24 fits passed**, including all six completed-control
fits and eight of the 15 originally unfinished primary fits. The three unresolved
stretches still lack complete comparisons. The original public findings remain
**12 globe preferences, zero flat preferences, 41 unresolved**.

This audit reads sealed results and journals only. It makes no new predictions or
fits, and changes no scientific labels. The {summary['native_sweeps']:,} charged sweeps
are well below the 14,448 ceiling; the unused allowance cannot be reused.

## Why the nine failures differ

- **Four early stability failures:** the saved gradient passed, but a bounded
  linear correction did not meet the unchanged measurement-stability requirement.
- **Four early stationarity failures:** the optimizer stopped on parameter-step
  size while the independently checked gradient remained excessive.
- **One budget failure:** the perturbed disc fit remained far from stationary
  when its fitting allowance was spent.

All eight early exits used the optimizer's `xtol` parameter-step test. Small
parameter steps are therefore insufficient evidence of completion. None of the
four failed stability probes reached a fresh nonlinear correction measurement:
they were rejected by the linear prediction first. Whether those corrections
improve the actual observations is not saved and cannot be inferred here.

| Stretch prefix | Processing case | Model / role | Evaluations | Gradient / limit | Probe result |
|---|---|---|---:|---:|---|
{table}

A gradient/limit ratio below one passes stationarity. It does not establish
measurement stability. Three of the four failed stability probes predict tiny
cost changes while predicting residual changes above the allowed limit; the
fourth predicts a larger cost improvement as well.

The failed Jacobians have a median condition ratio of
**{result['median_failed_condition']:.3g}**. That measures the disparity between
strong and weak local parameter combinations; it is a warning about numerical
sensitivity, not proof of its cause. Saved right singular vectors and complete
Jacobians are absent here, so the weak combinations cannot be reconstructed.
The dominant remaining gradients include gain/offset/gravity combinations and
near-boundary calibration coordinates.

One accepted fit passed three stable callbacks although its linear probe failed.
That is permitted by the frozen rule, but shows that callback stability and full
linear-correction stability are different tests. It must remain visible in the
next qualification; this audit does not change either tolerance to improve counts.

## Next numerical test

Screen a genuinely different bounded step strategy on deterministic equations
with known optima, coupled weak directions and near-boundary starts. Preserve the
same gradient, cost and measurement-stability requirements. Compare objective and
predicted observations, including failed tests. Do not select a strategy by its
preferred Earth model. An observed diagnostic must then record rejected steps,
fresh correction behavior and local tangents under a separately frozen finite
allowance. No new observed fit or all-41 rollout is authorized by this audit.

## Reproduce

Run from the repository root:

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-recovery-diagnosis-20261012/build_report.py
```

The builder checks the original completion seal, manifest, summary and both
charged journals. `fits.csv` preserves every accepted and failed result; the
receipt hashes inputs, audit software and generated artifacts. Original data and
completed trial outputs remain untouched.
'''
    (GUIDE/'README.md').write_text(text)
    artifacts = {name: hashlib.sha256((GUIDE/name).read_bytes()).hexdigest()
                 for name in ('README.md', 'fits.csv', 'diagnosis.json')}
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (Path(__file__), ROOT/'analysis/lll/ilvis0_recovery_diagnosis.py',
                         ROOT/'analysis/tests/test_ilvis0_recovery_diagnosis.py')}
    (GUIDE/'receipt.json').write_text(json.dumps(dict(inputs=hashes, sources=sources,
                artifacts=artifacts, observed_fit_starts=0, native_predictions=0), indent=2,
                sort_keys=True)+'\n')
    print(json.dumps({k: result[k] for k in ('starts', 'native_sweeps', 'counts',
                                           'control_passed', 'recovered_primary_fits')}))


if __name__ == '__main__':
    main()
