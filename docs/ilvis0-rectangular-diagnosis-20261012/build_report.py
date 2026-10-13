# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reproduce an audit from sealed saved tangents; no native observation calls."""
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics

import numpy as np
import scipy

from lll import ilvis0_recovery_diagnosis as saved
from lll import ilvis0_rectangular_diagnosis as audit

ROOT = Path(__file__).resolve().parents[2]
GUIDE = Path(__file__).resolve().parent
RUNTIME = ROOT/'data/ilvis0-rectangular-recovery-trial-v2-20261012'
PREVIOUS = ROOT/'data/ilvis0-convergence-recovery-trial-20261012'


def main():
    summary, inputs = saved.load_completed(RUNTIME)
    previous, previous_inputs = saved.load_completed(PREVIOUS)
    manifest = json.loads((RUNTIME/'manifest.json').read_text())
    roles = {t['identity']: t['role'] for t in manifest['proposal']['tasks']}
    rows = []
    for identity, fit in sorted(summary['results'].items()):
        value = audit.load_linearization(RUNTIME, fit)
        inputs[fit['linearization_file']] = fit['linearization_sha256']
        if (value['active_parameters'] != fit['active_parameters']
                or value['normalized_parameters'] != fit['normalized_parameters']):
            raise ValueError('local tangent disagrees with saved fit')
        residual = np.array(value['residual'])
        jac = np.array(value['jacobian'])
        if not np.isclose(residual@residual, fit['residual_sum_squares'], rtol=1e-12, atol=1e-12):
            raise ValueError('local cost disagrees with saved fit')
        audit.check_saved_gradient(value, fit['gradient'])
        row = saved.inspect_fit(identity, fit)
        row['task_role'] = roles[identity]
        row['local'] = audit.inspect_linearization(value)
        row['previous_converged'] = previous['results'][identity]['converged']
        trial = [t for t in fit['evaluation_trace'] if not t['fresh']]
        row['last_optimizer_step'] = trial[-1]['normalized_step_norm'] if trial else None
        rows.append(row)
    failed = [r for r in rows if not r['converged']]
    early = [r for r in failed if r['failure_class'] != 'budget_exhausted']
    counts = collections.Counter(r['failure_class'] for r in rows)
    result = dict(version=audit.VERSION, rows=rows, counts=dict(counts),
                  archived_passed=sum(r['converged'] for r in rows),
                  previous_archived_passed=sum(r['previous_converged'] for r in rows),
                  early_count=len(early),
                  early_with_roundoff_bound=sum(bool(r['local']['near_outward_parameters']) for r in early),
                  local_original_stationary=sum(r['local']['original']['stationarity_passed'] for r in rows),
                  local_snapped_stationary=sum(r['local']['snapped']['stationarity_passed'] for r in rows),
                  snap_tolerance=audit.SNAP_TOLERANCE,
                  maximum_affine_evaluations=audit.MAXIMUM_EVALUATIONS,
                  median_failed_condition=statistics.median(r['local']['condition'] for r in failed
                                                           if r['local']['condition'] is not None),
                  observed_fit_starts=0, native_predictions=0, original_labels_changed=False,
                  scientific_decision='abstain')
    (GUIDE/'diagnosis.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    flat = [dict(identity=r['identity'], role=r['task_role'], archived_passed=r['converged'],
                 previous_archived_passed=r['previous_converged'], failure=r['failure_class'],
                 evaluations=r['evaluations'], last_optimizer_step=r['last_optimizer_step'],
                 stationarity_ratio=r['stationarity_ratio'], probe_reason=r['probe_reason'],
                 near_outward_count=len(r['local']['near_outward_parameters']),
                 condition=r['local']['condition'],
                 dominant_gradient=r['local']['dominant_gradient_parameter'],
                 weak_parameters=';'.join(v['parameter'] for v in r['local']['weakest_direction'][:3]),
                 local_original_cost=r['local']['original']['cost'],
                 local_snapped_cost=r['local']['snapped']['cost'],
                 local_reference_cost=r['local']['reference']['cost'],
                 local_original_stationary=r['local']['original']['stationarity_passed'],
                 local_snapped_stationary=r['local']['snapped']['stationarity_passed'],
                 maximum_snap=r['local']['snap_maximum_change']) for r in rows]
    with (GUIDE/'fits.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat[0]))
        writer.writeheader(); writer.writerows(flat)
    table = '\n'.join(f"| {r['segment_id'][:8]} / {r['case_id'].removeprefix('bias1_')} | "
                      f"{r['model']} / {r['role']} | {r['evaluations']} | "
                      f"{r['stationarity_ratio']:.3g} | "
                      f"{r['local']['original']['stationarity_passed']} → "
                      f"{r['local']['snapped']['stationarity_passed']} |" for r in failed)
    weak = collections.Counter(v['parameter'] for r in failed
                               for v in r['local']['weakest_direction'][:3])
    weak_text = ', '.join(f'{name} ({n}/{len(failed)})' for name, n in weak.most_common(5))
    text = f'''# Why the rectangular recovery trial stalled

The completed trial passed **8 of 24 archival fits**: all six completed controls,
two of fifteen unfinished primary fits, and none of three perturbed repeats.
No test stretch became fully resolved. The preceding continuation method passed
15/24; the rectangular method did not improve recovery. Original findings remain
**12 globe preferences, zero completed flat preferences and 41 unresolved stretches**.

This audit verifies sealed summaries, journals and every saved local residual/Jacobian.
It reads no original aircraft observations, performs no native integrations or new
archival fits, and changes no scientific labels. Small affine-system solves below
are numerical diagnostics, not additional flight results.

## Two failure mechanisms

- **{counts['early_stationarity_failure']} early gradient failures:** the optimizer
  stopped on parameter-step size while the independent gradient check still failed.
- **{counts['early_stability_failure']} early stability failures:** the gradient passed,
  but the saved local correction changed predicted observations beyond the stability limit.
- **{counts['budget_exhausted']} exhausted fits:** perturbed starts spent their allowance
  without satisfying stationarity.

Of the {len(early)} early failures, **{result['early_with_roundoff_bound']}** have at least
one outward-pointing gradient on a coordinate less than 1e-12 inside its bound.
Many distances are one floating-point step. Such a coordinate can restrict the
optimizer's initial feasible step even when other coordinates still need to move.
Passed controls can also have near-bound coordinates; proximity alone does not
explain or invalidate a fit.

## Independently reproduced boundary stall

A two-coordinate control has residuals `(x−2, 2y−0.4)` inside the unchanged box
`−1 ≤ x,y ≤ 1`. Its exact bounded answer is `(1, 0.2)`, with squared residual cost 1.
Starting one floating-point step below `x=1` with `y=0` makes the rectangular solver
stop after two evaluations at cost 1.16, before correcting `y`. Starting exactly at
`x=1` recovers cost 1. This isolates a numerical boundary effect without aircraft
physics, unknown instruments or an Earth-model preference.

## Does the same explanation hold on the saved flight tangents?

For each saved point `u₀`, the audit holds the recorded residual `r₀` and Jacobian `J`
fixed and solves **`r(u) = r₀ + J(u−u₀)`**. The two starts differ only by moving
coordinates within 1e-12 of ±1 to their exact bounds. The physical parameter box,
gradient threshold, optimizer settings and 200-evaluation limit remain unchanged.
A bounded linear least-squares calculation supplies a separate local reference.

Across all 24 saved systems, the original start passes the gradient check in
**{result['local_original_stationary']}/24** cases; the exact-bound start passes in
**{result['local_snapped_stationary']}/24**. These are *local linear* completion counts,
not recovered archival fits or passes of the full nonlinear stability gate.

| Stretch / processing | Model / start | Archival evaluations | Gradient / limit | Local gradient: original → exact-bound |
|---|---|---:|---:|---|
{table}

`True` means the local affine solve passed the same gradient threshold. CSV and
JSON retain all 24 cases, objective values, bound movements and reference costs,
including local failures.

## Weak directions and interpretation

The failed saved Jacobians have a median condition ratio of
**{result['median_failed_condition']:.3g}**. Strong and weak parameter combinations
therefore act on markedly different scales. The most frequent coordinates among
the three largest components of the weakest directions are: {weak_text}.
Those directions describe correlated local combinations, not individually measured
instrument errors. Column-normalized spectra and column correlations are also saved.

An affine model is exact only for these saved linear equations. It cannot establish
that a sizeable local correction improves the actual nonlinear trajectory. The
audit does not test derivative accuracy, receiver-time discontinuities, changing
calibration or global optimality. It cannot promote any of the sixteen failed fits.

## Next qualification

Test boundary handling on known nonlinear optima and correlated, nearly singular
controls while retaining the existing feasible bounds and acceptance tolerances.
Compare objective and predicted-observation recovery from predetermined starts.
Only a separately frozen and budgeted observed-data trial can establish whether a
numerical repair recovers the unfinished stretches. The exhausted perturbed starts
also require attention; exact-bound initialization is not assumed to solve them.

## Reproduce

From the repository root:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-rectangular-diagnosis-20261012/build_report.py
```

The report receipt hashes both completed input studies, all local tangent artifacts,
audit software and generated outputs, and records the numerical environment.
Local optimizer counts describe that environment; they are not guaranteed across
platforms. The audit preserves the original trial's source snapshots.
'''
    (GUIDE/'README.md').write_text(text)
    sources = [Path(__file__), ROOT/'analysis/lll/ilvis0_rectangular_diagnosis.py',
               ROOT/'analysis/tests/test_ilvis0_rectangular_diagnosis.py',
               ROOT/'analysis/lll/ilvis0_recovery_diagnosis.py',
               ROOT/'analysis/lll/ilvis0_solver_refinement.py']
    receipt = dict(inputs={str(RUNTIME.relative_to(ROOT)/n): h for n, h in inputs.items()},
                   previous_inputs={str(PREVIOUS.relative_to(ROOT)/n): h for n, h in previous_inputs.items()},
                   sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                   artifacts={n: hashlib.sha256((GUIDE/n).read_bytes()).hexdigest()
                              for n in ('README.md', 'diagnosis.json', 'fits.csv', 'PLAN.md')},
                   environment=dict(python=platform.python_version(), numpy=np.__version__,
                                    scipy=scipy.__version__, platform=platform.platform(),
                                    threads={k: os.environ.get(k) for k in
                                             ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS')}),
                   observed_fit_starts=0, native_predictions=0)
    (GUIDE/'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: result[k] for k in ('counts', 'early_with_roundoff_bound',
                     'local_original_stationary', 'local_snapped_stationary', 'median_failed_condition')}))


if __name__ == '__main__':
    main()
